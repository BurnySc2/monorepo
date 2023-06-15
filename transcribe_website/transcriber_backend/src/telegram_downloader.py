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

from src.models.db import Status, TelegramMessage, db  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.TelegramDownloader

# Supress pyrogram messages that are caught anyway
logging.disable()

# Exclude debug logging messages
logger.remove()
logger.add(sys.stderr, level="INFO")


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
    async def download_one(worker_id: int | None = None) -> None:
        # Get a new message
        with orm.db_session():
            # No message in queue
            message: TelegramMessage | None = TelegramMessage.get_one_queued()
            if message is None:
                return
            # File already exists locally
            if message.download_completed:
                message.download_status = Status.COMPLETED.name
                message.downloaded_file_path = message.relative_path
                return
            message.download_status = Status.ACCEPTED_TO_DOWNLOAD.name

            # Find duplicates based on file size and duration
            duplicates_count = orm.count(
                m for m in TelegramMessage if (
                    m.file_size_bytes == message.file_size_bytes and m.file_duration_seconds == message.
                    file_duration_seconds and m.download_status in [Status.COMPLETED.name, Status.DOWNLOADING.name]
                )
            )
            if duplicates_count > 0:
                message.download_status = Status.DUPLICATE.name
                return
            # No return means no duplciate was found, start download
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
            with orm.db_session():
                message = TelegramMessage[message.id]
                message.download_status = Status.ERROR_DOWNLOADING.name
            return
        up_to_date_media: Video | Audio | Photo | None = (
            up_to_date_message.video or up_to_date_message.audio or up_to_date_message.photo
        )
        if up_to_date_media is None:
            with orm.db_session():
                message = TelegramMessage[message.id]
                message.download_status = Status.ERROR_DOWNLOADING.name
            return

        # Attempt to download file
        # pyre-fixme[9]
        data: BytesIO | None = await DownloadWorker.client.download_media(
            message=up_to_date_media.file_id,
            in_memory=True,
        )
        if data is None or data.getvalue() == b"":
            # Error again, file not downloadable
            logger.warning(f"Unable to download {message.link}")
            with orm.db_session():
                message = TelegramMessage[message.id]
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
                        message = TelegramMessage[message.id]
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
        # TODO what if file exists
        if message.output_file_path.is_file():
            logger.error(f"File already exists {message.output_file_path.absolute()}")
            return
        message.temp_download_path.rename(message.output_file_path)
        # Set modified date to message date
        os.utime(message.output_file_path, (message.message_date.timestamp(), message.message_date.timestamp()))

        # Mark message as "completed"
        with orm.db_session():
            message = TelegramMessage[message.id]
            message.download_status = Status.COMPLETED.name
            message.downloaded_file_path = message.relative_path

        logger.debug(f"{worker_id} Done downloading {message.output_file_path.absolute()}")


# Cache channels to list of message_ids to prevent multiple small select queries
add_to_queue_cache: dict[str, set[int]] = {}


def load_message_ids_to_cache(channel_id: str) -> None:
    if channel_id not in add_to_queue_cache:
        with orm.db_session():
            message_ids: list[int] = orm.select(m.message_id for m in TelegramMessage if m.channel_id == channel_id)
            add_to_queue_cache[channel_id] = set(message_ids)


async def add_to_queue(
    message: Message,
    channel_id: str,
) -> None:
    """Parse the given message and media-attachment and add information to the database."""
    media: Audio | Video | Photo = message.audio or message.video or message.photo
    media_class_name = media.__class__.__name__
    with orm.db_session():
        # Don't add same message_id twice
        if message.id in add_to_queue_cache[channel_id]:
            return

        new_telegram_message: TelegramMessage = TelegramMessage(
            channel_id=channel_id,
            message_id=message.id,
            message_date=message.date,
            link=message.link,
            download_status=Status.UNKNOWN.name,
        )
        load_message_ids_to_cache(channel_id)
        add_to_queue_cache[channel_id].add(message.id)

        new_telegram_message.media_type = media_class_name
        new_telegram_message.file_unique_id = media.file_unique_id
        new_telegram_message.file_size_bytes = media.file_size
        if isinstance(media, (Audio, Video)):
            new_telegram_message.file_duration_seconds = media.duration
            # Duplicate due to file size and file duration
            if orm.exists(
                m for m in TelegramMessage
                if m.file_size_bytes == media.file_size and m.file_duration_seconds == media.duration
            ):
                new_telegram_message.download_status = Status.DUPLICATE.name
                return
        if isinstance(media, (Photo, Video)):
            new_telegram_message.file_height = media.height
            new_telegram_message.file_width = media.width

        # Duplicate due to file_unique_id
        if orm.exists(m for m in TelegramMessage if m.file_unique_id == media.file_unique_id):
            new_telegram_message.download_status = Status.DUPLICATE.name
            return

        # Mark as queued on next run
        new_telegram_message.download_status = Status.FILTERED.name
    return


async def download_messages() -> None:
    for channel_id in SECRETS.channel_ids:
        done, total = TelegramMessage.get_count()
        logger.info(f"{done} / {total} Grabbing messages from channel: {channel_id}")
        previous_oldest_message_id = -1
        for _ in range(50):
            oldest_message_id: int = TelegramMessage.get_oldest_message_id(channel_id)
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
                    load_message_ids_to_cache(channel_id)
                    if message.id in add_to_queue_cache[channel_id]:
                        continue
                    # TODO documents
                    if message.photo or message.audio or message.video:
                        await add_to_queue(message, channel_id=channel_id)
                    else:
                        # Message has no media but add to database anyway to not parse it again
                        TelegramMessage(
                            channel_id=channel_id,
                            message_id=message.id,
                            message_date=message.date,
                            link=message.link,
                            download_status=Status.NO_MEDIA.name,
                        )


def requeue_interrupted_downloads():
    # Get and re-enqueue all messages from DB that were interrupted (or not finished) in last program run
    with orm.db_session():
        # Mark all queued messages as filtered
        db.execute(
            f"""
            UPDATE telegram_messages_to_download SET download_status = '{Status.FILTERED.name}'
            WHERE download_status = '{Status.QUEUED.name}';
            """
        )
    with orm.db_session():
        # Mark all messages that are not complete as queued which match filter
        db.execute(
            f"""
            UPDATE telegram_messages_to_download SET download_status = '{Status.QUEUED.name}' WHERE
            download_status NOT IN ('{Status.COMPLETED.name}', '{Status.DUPLICATE.name}')
            AND file_unique_id <> ''
            AND
            (
                    (media_type = 'Photo' AND 'Photo' IN {tuple(SECRETS.media_types)} 
                    AND {SECRETS.photo_min_file_size_bytes} <= file_size_bytes 
                    AND file_size_bytes <= {SECRETS.photo_max_file_size_bytes})
                OR
                    (media_type = 'Video' AND 'Video' IN {tuple(SECRETS.media_types)}
                    AND {SECRETS.video_min_file_size_bytes} <= file_size_bytes
                    AND file_size_bytes <= {SECRETS.video_max_file_size_bytes}
                    AND {SECRETS.video_min_file_duration_seconds} <= file_duration_seconds
                    AND file_duration_seconds <= {SECRETS.video_max_file_duration_seconds})
                OR
                    (media_type = 'Audio' AND 'Audio' IN {tuple(SECRETS.media_types)}
                    AND {SECRETS.audio_min_file_size_bytes} <= file_size_bytes
                    AND file_size_bytes <= {SECRETS.audio_max_file_size_bytes}
                    AND {SECRETS.audio_min_file_duration_seconds} <= file_duration_seconds
                    AND file_duration_seconds <= {SECRETS.audio_max_file_duration_seconds})
            );            
        """
        )


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
        done, total = TelegramMessage.get_count()
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