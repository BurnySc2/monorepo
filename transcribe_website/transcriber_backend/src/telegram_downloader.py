from __future__ import annotations

import asyncio
import datetime
import gc
import logging
import os
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import ClassVar

import humanize
from loguru import logger
from pony import orm  # pyre-fixme[21]
from pyrogram import Client
from pyrogram.types import Audio, Message, Photo, Video

from src.models.db import Status, TelegramChannel, TelegramMessage, db  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.TelegramDownloader

# Supress pyrogram messages that are caught anyway
logging.disable()

# Exclude debug logging messages
logger.remove()
logger.add(sys.stderr, level="INFO")

# {channel_id: {message_id: file_id}}
file_ids_cache: dict[str, dict[int, str]] = {}


def update_file_ids_cache(channel_id: str, messages: list[Message], message_ids: list[int]) -> None:
    """Update file_ids_cache with new messages."""
    if channel_id not in file_ids_cache:
        file_ids_cache[channel_id] = {}
    for message_id in message_ids:
        file_ids_cache[channel_id][message_id] = "UNKNOWN"
    for message in messages:
        media: Audio | Video | Photo | None = message.audio or message.video or message.photo
        if media is None:
            file_ids_cache[channel_id][message.id] = "UNKNOWN"
            continue
        file_ids_cache[channel_id][message.id] = media.file_id


def get_from_file_ids_cache(channel_id: str, message_id: int) -> str | None:
    """Get file_id from cache."""
    if channel_id in file_ids_cache and message_id in file_ids_cache[channel_id]:
        return file_ids_cache[channel_id][message_id]


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
    async def extract_audio_from_video(message: TelegramMessage, data_or_path: BytesIO | Path) -> BytesIO:
        message.temp_download_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data_or_path, BytesIO):
            logger.debug(
                f"Started processing audio ({message.file_size_bytes} b) "
                f"{message.output_file_path.absolute()}"
            )
            extracted_mp3_data: BytesIO = await DownloadWorker.extract_mp3_from_video(data_or_path)

            if len(extracted_mp3_data.getbuffer()) >= 200:
                logger.debug(
                    f"Finished processing audio ({message.file_size_bytes} b) "
                    f"{message.output_file_path.absolute()}"
                )
                return extracted_mp3_data
            else:
                # Write to file because ffmpeg can't read this video in one go and needs to seek
                with message.temp_download_path.open("wb") as f:
                    f.write(data_or_path.getbuffer())
                data_or_path = message.temp_download_path
        # Try again from file
        extracted_mp3_data: BytesIO = await DownloadWorker.extract_mp3_from_video(data_or_path)
        # Delete file after extracting the audio
        message.temp_download_path.unlink()
        logger.debug(
            f"Finished processing audio ({message.file_size_bytes} b) "
            f"{message.output_file_path.absolute()}"
        )
        return extracted_mp3_data

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
            # pyre-fixme[6]
            stdout_data, _ = await proc.communicate(data_or_path.getbuffer())
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
            message: TelegramMessage | None = TelegramMessage.get_one_queued()
            if message is None:
                # No message in queue
                return
            # Duplicate due to file_unique_id
            if orm.exists(
                m for m in TelegramMessage
                if m.file_unique_id == message.file_unique_id and m.message_id != message.message_id
            ):
                message.download_status = Status.DUPLICATE.name
                logger.debug(f"Duplicate found: {message.link}")
                return
            # Find duplicates based on file size and duration
            duplicates_exist = orm.exists(
                m for m in TelegramMessage if (
                    m.file_size_bytes == message.file_size_bytes
                    and m.file_duration_seconds == message.file_duration_seconds and m.download_status in
                    [Status.COMPLETED.name, Status.DOWNLOADING.name] and m.message_id != message.message_id
                )
            )
            if duplicates_exist:
                message.download_status = Status.DUPLICATE.name
                logger.debug(f"Duplicate found: {message.link}")
                return
            # File already exists locally
            if message.download_completed:
                message.download_status = Status.COMPLETED.name
                message.downloaded_file_path = message.relative_path
                logger.warning(f"File already exists: {message.link}")
                return
            # No return means no duplciate was found, start download
            message.download_status = Status.DOWNLOADING.name

        # Get file id from cache or update cache
        file_id = get_from_file_ids_cache(message.channel_id, message.message_id)
        if file_id == "UNKNOWN":
            # File id has been checked before and is not available, don't batch download again
            with orm.db_session():
                message = TelegramMessage[message.id]
                message.download_status = Status.ERROR_DOWNLOADING.name
            return
        if file_id is None:
            two_hundred_message_ids: list[int] = TelegramMessage.get_n_queued_by_channel(message.channel_id)
            if len(two_hundred_message_ids) > 200:
                raise ValueError("The api does not allow more than 200 messages to be downloaded at once.")
            # pyre-fixme[9]
            up_to_date_messages: list[Message] = await DownloadWorker.client.get_messages(
                chat_id=message.channel_id,
                message_ids=two_hundred_message_ids,
                replies=0,
            )
            update_file_ids_cache(message.channel_id, up_to_date_messages, two_hundred_message_ids)
            file_id = get_from_file_ids_cache(message.channel_id, message.message_id)
            if file_id is None or file_id == "UNKNOWN":
                with orm.db_session():
                    message = TelegramMessage[message.id]
                    message.download_status = Status.ERROR_DOWNLOADING.name
                return

        # Attempt to download file
        logger.debug(
            f"{worker_id} Started downloading ({message.file_size_bytes} b) {message.output_file_path.absolute()}"
        )
        message.temp_download_path.parent.mkdir(parents=True, exist_ok=True)
        download_to_memory = (
            SECRETS.extract_audio_from_videos and message.media_type == "Video" and message.file_size_bytes < 2**30
        )  # More than 1 gb means download to file
        if download_to_memory:
            # pyre-fixme[9]
            data: BytesIO | None = await DownloadWorker.client.download_media(
                message=file_id,
                in_memory=True,
            )
            if data is None or data.getbuffer() == b"":
                # Error, file not downloadable
                logger.warning(f"Unable to download {message.link}")
                TelegramMessage.update_status(message.id, Status.ERROR_DOWNLOADING)
                return
            # Extract mp3 from video file in memory via ffmpeg
            extracted_mp3_data = await DownloadWorker.extract_audio_from_video(message, data)
            if len(extracted_mp3_data.getbuffer()) < 200:
                logger.warning(f"Unable to extract audio {message.link}")
                TelegramMessage.update_status(message.id, Status.ERROR_EXTRACTING_AUDIO)
                return
            # Try to free memory where possible
            del data
            gc.collect()
            # Write extracted mp3 file
            with message.temp_download_path.open("wb") as f:
                f.write(extracted_mp3_data.getbuffer())
        else:
            # Download to file
            await DownloadWorker.client.download_media(
                message=file_id,
                file_name=str(message.temp_download_path.absolute()),
            )
            if not message.temp_download_path.is_file():
                # File not downloadable
                logger.warning(f"Unable to download {message.link}")
                TelegramMessage.update_status(message.id, Status.ERROR_DOWNLOADING)
                return
            # File was larger than limit, extract mp3 from video
            if SECRETS.extract_audio_from_videos and message.media_type == "Video":
                extracted_mp3_data = await DownloadWorker.extract_audio_from_video(message, message.temp_download_path)
                if len(extracted_mp3_data.getbuffer()) < 200:
                    logger.warning(f"Unable to extract audio {message.link}")
                    TelegramMessage.update_status(message.id, Status.ERROR_EXTRACTING_AUDIO)
                    return
                with message.temp_download_path.open("wb") as f:
                    f.write(extracted_mp3_data.getbuffer())

        # Rename to wanted file name and move to proper directory
        message.output_file_path.parent.mkdir(parents=True, exist_ok=True)
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
            # Get actual size of mp3 file
            if message.media_type == "Video" and SECRETS.extract_audio_from_videos:
                message.extracted_mp3_size_bytes = message.output_file_path.stat().st_size

        logger.debug(f"{worker_id} Done downloading {message.output_file_path.absolute()}")
        # Uncomment when running scalene to run 1 download
        # exit(0)


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
        if isinstance(media, (Photo, Video)):
            new_telegram_message.file_height = media.height
            new_telegram_message.file_width = media.width
        # Mark as queued on next run
        new_telegram_message.download_status = Status.FILTERED.name
    return


async def parse_channel_messages() -> None:
    with orm.db_session():
        done_channels = set(orm.select(c.channel_id for c in TelegramChannel if c.done_parsing))
        channels_that_may_have_new_messages = set(
            orm.select(
                c.channel_id for c in TelegramChannel
                if c.last_parsed < datetime.datetime.now() - datetime.timedelta(days=1)
            )
        )
    for channel_id in SECRETS.channel_ids:
        channel_has_been_parsed_completely = channel_id in done_channels
        channel_has_new_messages = channel_id in channels_that_may_have_new_messages
        if channel_has_been_parsed_completely and not channel_has_new_messages:
            continue
        with orm.db_session():
            channel: TelegramChannel | None = TelegramChannel.get(channel_id=channel_id)
            if channel is None:
                # Create channel entry
                TelegramChannel(channel_id=channel_id)

        logger.info(f"Grabbing messages from channel: {channel_id}")
        previous_oldest_message_id = -1
        try:
            for _ in range(50):  # Download in chunks of 1000 message
                if not channel_has_been_parsed_completely:
                    # Work your way back to the oldest message
                    oldest_message_id: int = TelegramMessage.get_oldest_message_id(channel_id)
                else:
                    # Try to get new messages
                    oldest_message_id: int = TelegramMessage.get_newest_message_id(channel_id) + 1000

                # Detect if channel has been parsed completely
                if previous_oldest_message_id == oldest_message_id:
                    with orm.db_session():
                        channel: TelegramChannel = TelegramChannel.get(channel_id=channel_id)  # pyre-fixme[35]
                        channel.done_parsing = True
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
                    current_message_count = 0
                    # pyre-fixme[16]
                    async for message in messages_iter:
                        current_message_count += 1
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
                        if current_message_count < 5 and message.id == oldest_message_id:
                            # We reached the oldest message in a few iterations, although we requested 1000 apart
                            # This means there were not many new messages
                            # pyre-fixme[35]
                            channel: TelegramChannel = TelegramChannel.get(channel_id=channel_id)
                            channel.last_parsed = datetime.datetime.utcnow()
                            raise StopIteration
        except StopIteration:
            # Exit inner loop because latest messages have been grabbed
            pass


def requeue_interrupted_downloads():
    # Get and re-enqueue all messages from DB that were interrupted (or not finished) in last program run
    with orm.db_session():
        # Mark all queued messages as filtered
        status_tuples = (
            Status.QUEUED.name,
            Status.DOWNLOADING.name,
        )
        db.execute(
            f"""
            UPDATE telegram_messages_to_download SET download_status = '{Status.FILTERED.name}'
            WHERE download_status in {status_tuples};
            """
        )
    with orm.db_session():
        # Mark all messages that are not complete as queued which match filter
        status_tuples = (
            Status.COMPLETED.name,
            Status.DUPLICATE.name,
            Status.ERROR_DOWNLOADING.name,
            Status.ERROR_EXTRACTING_AUDIO.name,
        )
        accept_photo = str("Photo" in SECRETS.media_types).lower()
        accept_video = str("Video" in SECRETS.media_types).lower()
        accept_audio = str("Audio" in SECRETS.media_types).lower()
        db.execute(
            f"""
            UPDATE telegram_messages_to_download SET download_status = '{Status.QUEUED.name}' WHERE
            download_status NOT IN {status_tuples}
            AND file_unique_id <> ''
            AND
            (
                    (media_type = 'Photo' AND {accept_photo} 
                    AND {SECRETS.photo_min_file_size_bytes} <= file_size_bytes 
                    AND file_size_bytes <= {SECRETS.photo_max_file_size_bytes})
                OR
                    (media_type = 'Video' AND {accept_video}
                    AND {SECRETS.video_min_file_size_bytes} <= file_size_bytes
                    AND file_size_bytes <= {SECRETS.video_max_file_size_bytes}
                    AND {SECRETS.video_min_file_duration_seconds} <= file_duration_seconds
                    AND file_duration_seconds <= {SECRETS.video_max_file_duration_seconds})
                OR
                    (media_type = 'Audio' AND {accept_audio}
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
    await parse_channel_messages()

    # Wait for downloads to finish
    while 1:
        # Check if jobs remaining and give status update
        done, total, done_bytes, total_bytes = TelegramMessage.get_count()
        logger.info(
            f"Waiting for jobs to finish: remaining count {total - done}, "
            f"remaining size {humanize.naturalsize(total_bytes - done_bytes)}, "
            f"total size {humanize.naturalsize(total_bytes)}"
        )
        if done == total:
            logger.info("Done with all downloads!")
            break
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
