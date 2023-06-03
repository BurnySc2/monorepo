import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from loguru import logger
from pony import orm  # pyre-fixme[21]
from pyrogram import Client
from pyrogram.types import Audio, Message, Photo, Video

from src.db import MessageModel, Status, audio_filter, photo_filter, video_filter
from src.secrets_loader import SECRETS


def check_message(message: MessageModel) -> str:
    """
    Check if a media passes the filters or even already exists.
    Otherwise mark it as queued to be processed to be downloaded.
    """
    output_path = Path(message.output_file)
    if output_path.is_file():
        return Status.COMPLETED.name
    elif audio_filter(message) and video_filter(message) and photo_filter(
        message
    ) and message.channel_id in SECRETS.channel_ids:
        return Status.QUEUED.name
    else:
        return Status.FILTERED.name


@dataclass
class DownloadWorker:
    client: ClassVar[Client]  # set after client has been created

    @staticmethod
    async def launch_workers(n: int = 10):
        """Start n download-workers that download files in parallel."""
        logger.info(f"Launching {n} workers")
        for i in range(n):
            worker = DownloadWorker()
            asyncio.create_task(worker.run())

    async def run(self):
        while 1:
            await asyncio.sleep(1)
            await DownloadWorker.download_one()

    @staticmethod
    async def download_one():
        # Get a new message
        with orm.db_session():
            message = MessageModel.get_one_queued()
            if message is None:
                return
            message.status = Status.DOWNLOADING.name
            output_path = Path(message.output_file)

        # done, total = MessageModel.get_count()
        # logger.info(f"{done} / {total} Download started: {message.output_file}")

        # Download the file to a temporary "downloading" directory
        download_file_path = SECRETS.output_folder_path / "downloading" / output_path.name
        download_file = str(download_file_path.absolute())
        await DownloadWorker.client.download_media(
            message=message.file_id,
            file_name=download_file,
        )

        # Rename to wanted file name and move to proper directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        download_file_path.rename(output_path)

        # Set modified date to message date
        os.utime(output_path, (message.message_date.timestamp(), message.message_date.timestamp()))

        # Mark message as "completed"
        with orm.db_session():
            message = MessageModel.get(
                channel_id=message.channel_id,
                message_id=message.message_id,
            )
            message.status = Status.COMPLETED.name

        # done, total = MessageModel.get_count()
        # logger.info(f"{done} / {total} Download completed: {message.output_file}")


async def add_to_queue(
    message: Message,
    media: Video | Audio | Photo,
    channel_id: str,
):
    """Parse the given message and media-attachment and add information to the database."""
    media_class_name = media.__class__.__name__
    with orm.db_session():
        # Don't add same file_unique_id twice
        message_from_db = MessageModel.get(
            channel_id=channel_id,
            file_unique_id=media.file_unique_id,
        )
        if message_from_db is not None:
            return

        message_from_db = MessageModel.get(
            channel_id=channel_id,
            message_id=message.id,
        )
        message_from_db.retry -= 1
        if not hasattr(media, "file_name") or media.file_name is None:
            if not hasattr(media, "mime_type"):
                # Unable to process media
                message_from_db.status = Status.MISSING_FILE_NAME.name
                return
            file_ending = media.mime_type.split("/")[-1]
            extracted_file_ending = f"{media.file_unique_id}.{file_ending}"
        else:
            extracted_file_ending = media.file_name
        message_from_db.output_file = str(
            (SECRETS.output_folder_path / channel_id / media_class_name / extracted_file_ending).absolute()
        )
        message_from_db.media_type = media_class_name
        message_from_db.file_id = media.file_id
        message_from_db.file_unique_id = media.file_unique_id
        message_from_db.file_name = extracted_file_ending
        message_from_db.file_size_bytes = media.file_size
        if isinstance(media, (Audio, Video)):
            message_from_db.file_duration_seconds = media.duration
        if isinstance(media, (Photo, Video)):
            message_from_db.file_height = media.height
            message_from_db.file_width = media.width

        message_from_db.status = check_message(message_from_db)


async def main(client: Client):
    # Get and re-enqueue all messages from DB that were interrupted (or not finished) in last program run
    logger.info("Checking for changed filters...")
    with orm.db_session():
        for message in orm.select(m for m in MessageModel if m.file_unique_id != ""):
            message.status = check_message(message)

    await client.start()
    await DownloadWorker.launch_workers(n=SECRETS.parallel_downloads_count)

    for channel_id in SECRETS.channel_ids:
        done, total = MessageModel.get_count()
        logger.info(f"{done} / {total} Grabbing messages from channel: {channel_id}")
        oldest_message_id: int = MessageModel.get_oldest_message_id(channel_id)
        # Get all messages (from newest to oldest), start with the oldest-parsed message
        messages_iter = client.get_chat_history(
            chat_id=channel_id,
            offset_id=oldest_message_id,
            limit=10000,
        )
        # This for loop can be in one session because it goes very quickly
        with orm.db_session():
            async for message in messages_iter:
                message: Message
                if message.empty is True:
                    continue
                # Don't add same message_id twice
                message_from_db = MessageModel.get(
                    channel_id=channel_id,
                    message_id=message.id,
                )
                if message_from_db is not None:
                    continue
                # logger.info(f"Inserting {channel_id} {message.id}")
                MessageModel(
                    channel_id=channel_id,
                    message_id=message.id,
                    message_date=message.date,
                    link=message.link,
                    status=Status.UNKNOWN.name,
                    retry=3,
                )
                if message.photo:
                    await add_to_queue(message, message.photo, channel_id=channel_id)
                elif message.audio:
                    await add_to_queue(message, message.audio, channel_id=channel_id)
                elif message.video:
                    await add_to_queue(message, message.video, channel_id=channel_id)
                # TODO documents
                else:
                    # Message has no media but add to database anyway to not parse it again
                    message_from_db = MessageModel.get(
                        channel_id=channel_id,
                        message_id=message.id,
                    )
                    message_from_db.status = Status.NO_MEDIA.name
    # Wait for downloads to finish
    while 1:
        await asyncio.sleep(5)
        # Check if jobs remaining and give status update
        done, total = MessageModel.get_count()
        if done == total:
            logger.info("Done with all downloads!")
            break
        logger.info(f"Waiting for jobs to finish: {done} / {total}")


if __name__ == "__main__":
    app = Client(
        name="media_downloader",
        api_id=SECRETS.api_id,
        api_hash=SECRETS.api_hash,
    )
    DownloadWorker.client = app
    asyncio.run(main(app))
