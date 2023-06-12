from __future__ import annotations

import asyncio
import logging
import os
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import ClassVar

from loguru import logger
from pony import orm  # pyre-fixme[21]
from pyrogram import Client
from pyrogram.types import Audio, Message, Photo, Video

sys.path.append(str(Path(__file__).parent.parent))
from src.db_telegram import MessageModel, Status, audio_filter, photo_filter, video_filter  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.TelegramDownloader

# Supress pyrogram messages that are caught anyway
logging.disable()

# Exclude debug logging messages
logger.remove()
logger.add(sys.stderr, level="INFO")


def check_message(message: MessageModel) -> str:
    """
    Check if a media passes the filters or even already exists.
    Otherwise mark it as queued to be processed to be downloaded.
    """
    if message.download_completed:
        if message.downloaded_file_path == "":
            relative_file_path = message.output_file_path.relative_to(SECRETS.output_folder)
            message.downloaded_file_path = str(relative_file_path)
        return Status.COMPLETED.name
    elif (
        audio_filter(message) and video_filter(message) and photo_filter(message)
        and SECRETS.media_min_date < message.message_date < SECRETS.media_max_date
        and message.channel_id in SECRETS.channel_ids
    ):
        return Status.QUEUED.name
    else:
        return Status.FILTERED.name


@dataclass
# pyre-fixme[13]
class DownloadWorker:
    client: ClassVar[Client]  # set after client has been created

    worker_id: int = 0

    @staticmethod
    async def launch_workers(n: int = 5):
        """Start n download-workers that download files in parallel."""
        logger.info(f"Launching {n} workers")
        for i in range(n):
            worker = DownloadWorker(worker_id=i + 1)
            _ = asyncio.create_task(worker.run(), name=f"{i}")

    async def run(self):
        while 1:
            await asyncio.sleep(1)
            try:
                await DownloadWorker.download_one(worker_id=self.worker_id)
            except Exception as e:
                # Catch errors by worker and end program
                logger.exception(e)
                sys.exit(1)

    @staticmethod
    async def extract_mp3_from_video(data_or_path: BytesIO | Path) -> BytesIO:
        if isinstance(data_or_path, BytesIO):

            command = [
                "ffmpeg",
                "-i",
                "-",
                "-vn",
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                "-f",
                "mp3",
                "-",
            ]
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout_data, _ = await proc.communicate(data_or_path.getvalue())
        elif isinstance(data_or_path, Path):
            command = [
                "ffmpeg",
                "-i",
                str(data_or_path.absolute()),
                "-vn",
                "-c:a",
                "libmp3lame",
                "-q:a",
                "2",
                "-f",
                "mp3",
                "-",
            ]
            proc = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout_data, _ = await proc.communicate()
        else:
            raise TypeError(f"Needs to be BytesIO or Path, was {type(data_or_path)}")
        return BytesIO(stdout_data)

    @staticmethod
    async def download_one(worker_id: int | None = None):
        # Get a new message
        with orm.db_session():
            message: MessageModel | None = MessageModel.get_one_queued()
            if message is None:
                return
            message.download_status = Status.ACCEPTED_TO_DOWNLOAD.name

        # Find duplicate in database - if found, mark this as duplicate
        with orm.db_session():
            for _duplicate in orm.select(
                # pyre-fixme[16]
                m for m in MessageModel if (
                    m.file_size_bytes == message.file_size_bytes and m.file_duration_seconds == message.
                    file_duration_seconds and m.download_status in [Status.COMPLETED.name, Status.DOWNLOADING.name]
                )
            ):
                # pyre-fixme[16]
                message = MessageModel[message.id]
                message.download_status = Status.DUPLICATE.name
                return
            # No return means no duplciate was found, start download
            message = MessageModel[message.id]
            message.download_status = Status.DOWNLOADING.name

        logger.debug(
            f"{worker_id} Started downloading ({message.file_size_bytes} b) {message.output_file_path.absolute()}"
        )

        # pyre-fixme[9]
        up_to_date_message: Message | None = await DownloadWorker.client.get_messages(
            chat_id=message.channel_id,
            message_ids=message.message_id,
            replies=0,
        )
        if up_to_date_message is None:
            return
        up_to_date_media: Video | Audio | Photo = (
            up_to_date_message.video or up_to_date_message.audio or up_to_date_message.photo
        )
        # pyre-fixme[9]
        data: BytesIO | None = await DownloadWorker.client.download_media(
            # message=message.file_id,
            message=up_to_date_media.file_id,
            in_memory=True,
        )
        if data is None or data.getvalue() == b"":
            # Error again, file not downloadable
            logger.warning(f"Unable to download {message.link}")
            with orm.db_session():
                message = MessageModel[message.id]
                message.download_status = Status.ERROR_DOWNLOADING.name
            return

        # Extract mp3 from mp4 file in memory via ffmpeg if SECRET.extract_audio_from_videos is True
        if SECRETS.extract_audio_from_videos and message.media_type == "Video":
            logger.debug(
                f"{worker_id} Started processing audio ({message.file_size_bytes} b) "
                f"{message.output_file_path.absolute()}"
            )
            extracted_mp3_data: BytesIO = await DownloadWorker.extract_mp3_from_video(data)

            if len(extracted_mp3_data.getvalue()) < 200:
                # Write to file because ffmpeg can't read this video in one go and needs to seek
                message.temp_download_path.parent.mkdir(parents=True, exist_ok=True)
                with message.temp_download_path.open("wb") as f:
                    f.write(data.getvalue())

                extracted_mp3_data: BytesIO = await DownloadWorker.extract_mp3_from_video(message.temp_download_path)

                # Delete file after extracting the audio
                message.temp_download_path.unlink()
                if len(extracted_mp3_data.getvalue()) < 200:
                    logger.warning(f"Unable to extract audio {message.link}")
                    with orm.db_session():
                        message = MessageModel[message.id]
                        message.download_status = Status.ERROR_EXTRACTING_AUDIO.name
                    return
            logger.debug(
                f"{worker_id} Finished processing audio ({message.file_size_bytes} b) "
                f"{message.output_file_path.absolute()}"
            )
            data = extracted_mp3_data

        # Write original data or (if enabled) extracted mp3 file
        message.temp_download_path.parent.mkdir(parents=True, exist_ok=True)
        with message.temp_download_path.open("wb") as f:
            f.write(data.getvalue())

        # Rename to wanted file name and move to proper directory
        message.output_file_path.parent.mkdir(parents=True, exist_ok=True)
        message.temp_download_path.rename(message.output_file_path)
        # Set modified date to message date
        os.utime(message.output_file_path, (message.message_date.timestamp(), message.message_date.timestamp()))

        # Mark message as "completed"
        relative_file_path = message.output_file_path.relative_to(SECRETS.output_folder)
        with orm.db_session():
            message = MessageModel[message.id]
            message.download_status = Status.COMPLETED.name
            message.downloaded_file_path = str(relative_file_path)

        logger.debug(f"{worker_id} Done downloading {message.output_file_path.absolute()}")


async def add_to_queue(
    message: Message,
    channel_id: str,
) -> MessageModel:
    """Parse the given message and media-attachment and add information to the database."""
    media: Audio | Video | Photo = message.audio or message.video or message.photo
    media_class_name = media.__class__.__name__
    with orm.db_session():
        # Don't add same file_unique_id twice
        # pyre-fixme[16]
        message_from_db: MessageModel | None = MessageModel.get(
            channel_id=channel_id,
            file_unique_id=media.file_unique_id,
        )
        if message_from_db is not None:
            # Update file_id if changed
            message_from_db.file_id = media.file_id
            message_from_db.file_unique_id = media.file_unique_id
            return message_from_db

        # Try to find from db, else create new row
        # pyre-fixme[35]
        message_from_db: MessageModel | None = MessageModel.get(
            channel_id=channel_id,
            message_id=message.id,
        )
        if message_from_db is None:
            # pyre-fixme[28]
            # pyre-fixme[35]
            message_from_db: MessageModel = MessageModel(
                channel_id=channel_id,
                message_id=message.id,
                message_date=message.date,
                link=message.link,
                download_status=Status.UNKNOWN.name,
            )

        # Attempt to find file ending and a file name
        # pyre-fixme[16]
        if not hasattr(media, "file_name") or media.file_name is None:
            if not hasattr(media, "mime_type"):
                # Unable to process media
                message_from_db.download_status = Status.MISSING_FILE_NAME.name
                return message_from_db
            # pyre-fixme[16]
            file_ending = media.mime_type.split("/")[-1]
            extracted_file_name = f"{media.file_unique_id}.{file_ending}"
        else:
            # pyre-fixme[16]
            extracted_file_name = media.file_name

        message_from_db.media_type = media_class_name
        message_from_db.file_id = media.file_id
        message_from_db.file_unique_id = media.file_unique_id
        message_from_db.file_name = extracted_file_name
        message_from_db.file_size_bytes = media.file_size
        if isinstance(media, (Audio, Video)):
            message_from_db.file_duration_seconds = media.duration
        if isinstance(media, (Photo, Video)):
            message_from_db.file_height = media.height
            message_from_db.file_width = media.width

        message_from_db.download_status = check_message(message_from_db)
    return message_from_db


async def download_messages() -> None:
    for channel_id in SECRETS.channel_ids:
        done, total = MessageModel.get_count()
        logger.info(f"{done} / {total} Grabbing messages from channel: {channel_id}")
        previous_oldest_message_id = -1
        for _ in range(50):
            oldest_message_id: int = MessageModel.get_oldest_message_id(channel_id)
            # Detect if channel has been parsed completely
            if previous_oldest_message_id == oldest_message_id:
                break
            previous_oldest_message_id = oldest_message_id

            # Get all messages (from newest to oldest), start with the oldest-parsed message
            messages_iter = DownloadWorker.client.get_chat_history(
                chat_id=channel_id,
                offset_id=oldest_message_id,
                limit=1000,
            )
            # This for loop can be in one session because it goes very quickly
            with orm.db_session():
                # pyre-fixme[16]
                async for message in messages_iter:
                    message: Message
                    if message.empty is True:
                        continue
                    # Don't add same message_id twice
                    # pyre-fixme[16]
                    message_from_db = MessageModel.get(
                        channel_id=channel_id,
                        message_id=message.id,
                    )
                    if message_from_db is not None:
                        continue
                    # TODO documents
                    if message.photo or message.audio or message.video:
                        await add_to_queue(message, channel_id=channel_id)
                    else:
                        # Message has no media but add to database anyway to not parse it again
                        # pyre-fixme[28]
                        MessageModel(
                            channel_id=channel_id,
                            message_id=message.id,
                            message_date=message.date,
                            link=message.link,
                            download_status=Status.NO_MEDIA.name,
                        )


def requeue_interrupted_downloads():
    # Get and re-enqueue all messages from DB that were interrupted (or not finished) in last program run
    with orm.db_session():
        for message in orm.select(
            m for m in MessageModel if m.file_unique_id != "" and m.download_status not in [
                Status.COMPLETED.name,
                Status.DUPLICATE.name,
            ]
        ).for_update():
            message: MessageModel
            message.download_status = check_message(message)


async def main():
    logger.info("Checking for changed filters...")
    requeue_interrupted_downloads()

    await DownloadWorker.client.start()

    await DownloadWorker.launch_workers(n=SECRETS.parallel_downloads_count)

    # Start parsing channels and messages
    await download_messages()

    # Wait for downloads to finish
    while 1:
        # Check if jobs remaining and give status update
        done, total = MessageModel.get_count()
        if done == total:
            logger.info("Done with all downloads!")
            break
        logger.info(f"Waiting for jobs to finish: {done} / {total}")
        await asyncio.sleep(60)


if __name__ == "__main__":
    current_folder = Path(__file__).parent.parent
    app = Client(
        name="media_downloader",
        api_id=SECRETS.api_id,
        api_hash=SECRETS.api_hash,
        # pyre-fixme[6]
        workdir=current_folder,
    )
    DownloadWorker.client = app
    asyncio.run(main(), debug=False)
