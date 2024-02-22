from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from queue import Queue
from threading import Lock, Semaphore
from typing import ClassVar

import humanize
import pyrogram
from loguru import logger
from psycopg.rows import class_row, namedtuple_row
from pyrogram import Client
from pyrogram.types import Message

from src.models.telegram_model2 import Status, TelegramMessage2
from src.secrets_loader import SECRETS as SECRETS_FULL
from src.sql.db import Queries, execute_query  # noqa: E402

SECRETS = SECRETS_FULL.TelegramDownloader

# Supress pyrogram messages that are caught anyway
logging.disable()

# Exclude debug logging messages
logger.remove()
logger.add(sys.stderr, level="INFO")


# Only run 'value' amount of ffmpeg processes at the same time
ffmpeg_sem = Semaphore(value=SECRETS.parallel_ffmpeg_count)


def media_ending(message: Message) -> str:
    if message.media.name == "VIDEO":
        return ".mp4"
    if message.media.name == "AUDIO":
        return ".mp3"
    if message.media.name == "PHOTO":
        return ".jpg"
    raise ValueError(f"Unknown media type: {message.media.name}")


def db_update_message_status(
    channel_id: str,
    message_ids: list[int],
    new_status: Status,
):
    execute_query(
        Queries.mark_messages_as,
        {
            "my_channel_id": channel_id,
            "message_ids": message_ids,
            "new_status": new_status.name,
        },
    )


def db_complede_message_download(
    channel_id: str,
    message_id: int,
    downloaded_file_path: str,
    extracted_mp3_size_bytes: int,
):
    execute_query(
        Queries.update_completed_message,
        {
            "my_channel_id": channel_id,
            "message_id": message_id,
            "downloaded_file_path": downloaded_file_path,
            "extracted_mp3_size_bytes": extracted_mp3_size_bytes,
            "new_status": Status.COMPLETED.name,
        },
    )


@dataclass
class DownloadWorker:
    client_lock: ClassVar[Lock] = Lock()
    # queue: ClassVar[Queue[Message]] = Queue()
    queue: ClassVar[Queue[Message]] = Queue(maxsize=100)

    worker_id: int = 0

    @staticmethod
    async def async_download_media(message: Message, download_path: Path):
        current_folder = Path(__file__).parent.parent
        with DownloadWorker.client_lock:
            client = Client(
                "media_downloader",
                api_id=SECRETS.api_id,
                api_hash=SECRETS.api_hash,
                # pyre-fixme[6]
                workdir=current_folder,
            )
            async with client:
                logger.info(f"Downloading media: {download_path.resolve()}")
                await client.download_media(
                    message=message.video.file_id,
                    file_name=str(download_path.resolve()),
                )
                logger.info(f"Done downloading media: {download_path.resolve()}")

    @staticmethod
    async def async_get_messages(channel_id: str, two_hundred_message_ids: list[int]):
        current_folder = Path(__file__).parent.parent
        with DownloadWorker.client_lock:
            client = Client(
                "media_downloader",
                api_id=SECRETS.api_id,
                api_hash=SECRETS.api_hash,
                # pyre-fixme[6]
                workdir=current_folder,
            )
            async with client:
                up_to_date_messages = await client.get_messages(
                    chat_id=channel_id,
                    message_ids=two_hundred_message_ids,
                    replies=0,
                )
                return up_to_date_messages

    @staticmethod
    def update_telegram_messages() -> None:
        # TODO Query get a message, sort by (channel, -message_id)

        # TODO If duplicate exists: m.file_unique_id == message.file_unique_id and m.message_id != message.message_id
        # skip, mark as duplicate if already other is marked as downloading or complete
        try:
            while 1:
                # # Wait for downloaders to finish their work
                # if DownloadWorker.queue.qsize() > 20:
                #     time.sleep(30)
                #     continue
                # get any message that is queued for download
                message: TelegramMessage2 = execute_query(
                    Queries.get_queued_message,
                    params={"my_limit": 1},
                    my_row_factory=class_row(TelegramMessage2),
                ).fetchone()
                # get 200 messages from such a channel
                two_hundred_messages: list = execute_query(
                    Queries.get_ids_of_200_messages_from_channel,
                    params={
                        "message_channel_id": message.channel_id,
                    },
                    my_row_factory=namedtuple_row,
                ).fetchall()
                two_hundred_message_ids: list[int] = [i.message_id for i in two_hundred_messages]
                if len(two_hundred_message_ids) > 200:
                    raise ValueError("The api does not allow more than 200 messages to be downloaded at once.")

                up_to_date_messages: list[Message] = []
                while len(up_to_date_messages) == 0:
                    try:
                        up_to_date_messages = asyncio.run(
                            DownloadWorker.async_get_messages(message.channel_id, two_hundred_message_ids)
                        )
                        # https://stackoverflow.com/questions/71773181/avoid-floodwait-in-python
                    except pyrogram.errors.exceptions.flood_420.FloodWait:
                        # Try again
                        time.sleep(5)
                    # except UsernameNotOccupied:
                    # TODO set messages to ERROR_CHANNEL_INACCESSIBLE

                # TODO Check: messages that were queried vs those that were received, which ones are missing?
                # mark those as FAILED

                # Mark them as downloading (or new status: ready to download)
                db_update_message_status(
                    channel_id=message.channel_id,
                    message_ids=two_hundred_message_ids,
                    new_status=Status.DOWNLOADING,
                )
                for telegram_message in up_to_date_messages:
                    assert telegram_message is not None
                    DownloadWorker.queue.put(telegram_message)
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            sys.exit(1)

    @staticmethod
    def extract_mp3_from_video(data_or_path: Path) -> BytesIO:
        if isinstance(data_or_path, BytesIO):
            raise NotImplementedError("This may fail so I removed it for simplicity")
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
            with ffmpeg_sem:
                proc = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                stdout_data, _ = proc.communicate()
        else:
            raise TypeError(f"Needs to be BytesIO or Path, was {type(data_or_path)}")
        return BytesIO(stdout_data)

    @staticmethod
    def downloader(worker_id: int | None = None) -> None:
        while 1:
            try:
                DownloadWorker.download_one()
                time.sleep(1)
            except Exception as e:  # noqa: BLE001
                logger.exception(e)
                sys.exit(1)

    @staticmethod
    def download_one() -> None:
        # TODO Refactor to allow audio and image download
        # Attempt to download file
        # Get a new message
        message: Message | None = DownloadWorker.queue.get()  # TODO add timeout? = queue not filling up = done
        if message is None:
            return
        temp_download_path = SECRETS.output_folder_path / "downloading" / f"{message.video.file_unique_id}.temp_file"
        temp_download_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Started downloading ({message.video.file_size} b) {temp_download_path.resolve()}")

        # Check if duplicate already has been downloaded, then mark this message as DUPLICATE
        count_duplicate = execute_query(
            Queries.count_duplicate,
            params={
                "my_file_unique_id": message.video.file_unique_id,
            },
        ).fetchone()[0]
        if count_duplicate > 0:
            db_update_message_status(
                channel_id=message.sender_chat.username,
                message_ids=[message.id],
                new_status=Status.DUPLICATE,
            )
            return

        # Download to file
        asyncio.run(DownloadWorker.async_download_media(message, temp_download_path))

        if not temp_download_path.is_file():
            # File not downloadable
            logger.warning(f"Unable to download {message.link}")
            db_update_message_status(
                channel_id=message.sender_chat.username,
                message_ids=[message.id],
                new_status=Status.ERROR_DOWNLOADING,
            )
            return

        # Extract mp3 from video
        if SECRETS.extract_audio_from_videos and message.media.name == "VIDEO":
            extracted_mp3_data = DownloadWorker.extract_mp3_from_video(temp_download_path)
            # Error when extracting
            if len(extracted_mp3_data.getbuffer()) < 200:
                logger.warning(f"Unable to extract audio {message.link}")
                db_update_message_status(
                    channel_id=message.sender_chat.username,
                    message_ids=[message.id],
                    new_status=Status.ERROR_EXTRACTING_AUDIO,
                )
                temp_download_path.unlink()
                return
            with temp_download_path.open("wb") as f:
                f.write(extracted_mp3_data.getbuffer())

        # Rename to wanted file name and move to proper directory
        if message.media.name == "VIDEO" and SECRETS.extract_audio_from_videos:
            output_file_path = (
                SECRETS.output_folder_path
                / message.sender_chat.username
                / "extracted_audio"
                / f"{message.video.file_unique_id}.mp3"
            )
        else:
            output_file_path = (
                SECRETS.output_folder_path
                / message.sender_chat.username
                / message.media.name.lower()
                / f"{message.video.file_unique_id}{media_ending(message)}"
            )
        output_file_path.parent.mkdir(parents=True, exist_ok=True)
        if output_file_path.is_file():
            logger.error(f"File already exists {output_file_path.resolve()}")
            return
        temp_download_path.rename(output_file_path)
        # Set modified date to message date
        os.utime(output_file_path, (message.date.timestamp(), message.date.timestamp()))

        logger.info(f"Done downloading {output_file_path.resolve()}")
        # Mark message as "completed"
        db_complede_message_download(
            channel_id=message.sender_chat.username,
            message_id=message.id,
            downloaded_file_path=str(output_file_path.relative_to(SECRETS.output_folder_path).resolve()),
            extracted_mp3_size_bytes=output_file_path.stat().st_size,
        )
        # Uncomment when running scalene to run 1 download
        # exit(0)


# async def parse_channel_messages() -> None:
#     with orm.db_session():
#         done_channels = set(orm.select(c.channel_id for c in TelegramChannel if c.done_parsing))
#         channels_that_may_have_new_messages = set(
#             orm.select(
#                 # TODO turn the timedelta argument into a variable setting: days_before_known_channels_are_reparsed
#                 c.channel_id
#                 for c in TelegramChannel
#                 if c.last_parsed < datetime.datetime.now() - datetime.timedelta(days=7)
#             )
#         )
#     for channel_id in SECRETS.channel_ids:
#         channel_has_been_parsed_completely = channel_id in done_channels
#         channel_has_new_messages = channel_id in channels_that_may_have_new_messages
#         if channel_has_been_parsed_completely and not channel_has_new_messages:
#             continue
#         with orm.db_session():
#             channel: TelegramChannel | None = TelegramChannel.get(channel_id=channel_id)
#             if channel is None:
#                 # Create channel entry
#                 TelegramChannel(channel_id=channel_id)

#         logger.info(f"Grabbing messages from channel: {channel_id}")
#         previous_oldest_message_id = -1
#         added_messages = 0
#         try:
#             for _ in range(50):  # Download in chunks of 1000 message
#                 if not channel_has_been_parsed_completely:
#                     # Work your way back to the oldest message
#                     oldest_message_id: int = TelegramMessage.get_oldest_message_id(channel_id)
#                 else:
#                     # Try to get new messages
#                     oldest_message_id: int | None = TelegramMessage.get_newest_message_id(channel_id)
#                     if oldest_message_id is None:
#                         logger.info(f"Channel is unavailable: {channel_id}")
#                         raise StopIteration
#                     oldest_message_id += 1000

#                 # Detect if channel has been parsed completely
#                 if previous_oldest_message_id == oldest_message_id:
#                     with orm.db_session():
#                         channel: TelegramChannel = TelegramChannel.get(channel_id=channel_id)
#                         channel.done_parsing = True
#                         channel.last_parsed = datetime.datetime.utcnow()
#                     break
#                 previous_oldest_message_id = oldest_message_id

#                 # Get all messages (from newest to oldest), start with the oldest-parsed message
#                 current_message_count = 0
#                 messages_iter = DownloadWorker.client.get_chat_history(
#                     chat_id=channel_id,
#                     offset_id=oldest_message_id,
#                     limit=1000,
#                 )
#                 # This for loop can be in one session because it goes very quickly
#                 with orm.db_session():
#                     async for message in messages_iter:
#                         current_message_count += 1
#                         message: Message
#                         if message.empty is True:
#                             continue
#                         # Don't add same message_id twice
#                         load_message_ids_to_cache(channel_id)
#                         if message.id in add_to_queue_cache[channel_id]:
#                             continue
#                         added_messages += 1
#                         # TODO documents
#                         if message.photo or message.audio or message.video:
#                             await add_to_queue(message, channel_id=channel_id)
#                         else:
#                             # Message has no media but add to database anyway to not parse it again
#                             TelegramMessage(
#                                 channel_id=channel_id,
#                                 message_id=message.id,
#                                 message_date=message.date,
#                                 link=message.link,
#                                 download_status=Status.NO_MEDIA.name,
#                             )
#                         if current_message_count < 5 and message.id == oldest_message_id:
#                             # We reached the oldest message in a few iterations, although we requested 1000 apart
#                             # This means there were not many new messages
#                             channel: TelegramChannel = TelegramChannel.get(channel_id=channel_id)
#                             channel.last_parsed = datetime.datetime.utcnow()
#                             raise StopIteration("Last message in channel has been grabbed")
#         except (TypeError, OSError) as e:
#             # https://github.com/BurnySc2/monorepo/issues/38
#             logger.error(f"Error with channel {channel_id}: {e}")
#         except UsernameNotOccupied:
#             # If any errors occur, skip parsing this channel
#             logger.error(f"Error with channel {channel_id}, username not occupied")
#         except StopIteration:
#             # Exit inner loop because latest messages have been grabbed
#             pass
#         if added_messages > 0:
#             logger.info(f"Added {added_messages} new messages for channel: {channel_id}")


def requeue_interrupted_downloads():
    # Get and re-enqueue all messages from DB that were interrupted (or not finished) in last program run
    _result = execute_query(
        # Mark all queued/downloading messages as filtered
        Queries.resume,
        {
            "status": Status.FILTERED.name,
            "queued_or_downloading": [
                Status.QUEUED.name,
                Status.DOWNLOADING.name,
            ],
        },
    )

    _result = execute_query(
        # Mark all messages that are not completed as queued which match filter
        Queries.mark_filtered,
        {
            # Which to resume
            "queued": Status.QUEUED.name,
            "status": [
                Status.COMPLETED.name,
                Status.DUPLICATE.name,
                Status.ERROR_DOWNLOADING.name,
                Status.ERROR_EXTRACTING_AUDIO.name,
            ],
            # Filter photo
            "accept_photo": "photo" in SECRETS.media_types,
            "photo_min_file_size_bytes": SECRETS.photo_min_file_size_bytes,
            "photo_max_file_size_bytes": SECRETS.photo_max_file_size_bytes,
            # Filter video
            "accept_video": "video" in SECRETS.media_types,
            "video_min_file_size_bytes": SECRETS.video_min_file_size_bytes,
            "video_max_file_size_bytes": SECRETS.video_max_file_size_bytes,
            "video_min_file_duration_seconds": SECRETS.video_min_file_duration_seconds,
            "video_max_file_duration_seconds": SECRETS.video_max_file_duration_seconds,
            # Filter audio
            "accept_audio": "audio" in SECRETS.media_types,
            "audio_min_file_size_bytes": SECRETS.audio_min_file_size_bytes,
            "audio_max_file_size_bytes": SECRETS.audio_max_file_size_bytes,
            "audio_min_file_duration_seconds": SECRETS.audio_min_file_duration_seconds,
            "audio_max_file_duration_seconds": SECRETS.audio_max_file_duration_seconds,
        },
    )


def status_update():
    # Wait for downloads to finish
    try:
        while 1:
            # Check if jobs remaining and give status update
            done_jobs, total_jobs, done_bytes, total_bytes = execute_query(
                Queries.status,
                params={
                    "done_status": [
                        Status.DUPLICATE.name,
                        Status.COMPLETED.name,
                    ],
                    "total_status": [
                        Status.QUEUED.name,
                        Status.DOWNLOADING.name,
                        Status.DUPLICATE.name,
                        Status.COMPLETED.name,
                    ],
                },
            ).fetchone()
            logger.info(
                f"Waiting for jobs to finish: remaining count {total_jobs - done_jobs}, "
                f"remaining size {humanize.naturalsize(total_bytes - done_bytes)}, "
                f"total size {humanize.naturalsize(total_bytes)}"
            )
            if done_jobs == total_jobs:
                logger.info("Done with all downloads!")
                break
            time.sleep(60)
    except Exception as e:  # noqa: BLE001
        logger.exception(e)
        sys.exit(1)


def list_all_joined_public_chats(min_users: int) -> None:
    """Yield all chats that this telegram user has joined."""
    with Client(
        "media_downloader",
        api_id=SECRETS.api_id,
        api_hash=SECRETS.api_hash,
        workdir=current_folder,
    ) as client:
        chats: list[tuple[str, int]] = []
        dialog: pyrogram.types.Dialog
        for dialog in client.get_dialogs():
            chat: pyrogram.types.Chat = dialog.chat
            # Not public
            if chat.username is None:
                continue
            # Private chat
            if chat.members_count is None:
                continue
            # Minimum not met
            if chat.members_count < min_users:
                continue
            chats.append((chat.username, chat.members_count))
    chats.sort(key=lambda i: i[1], reverse=True)
    names = [i[0] for i in chats]
    for name in names:
        print(f'"{name}",')


def main():
    logger.info("Checking for changed filters...")
    requeue_interrupted_downloads()

    # Print all connected channels
    # list_all_joined_public_chats(min_users=300)

    # Clear "downloading" folder
    for file in (SECRETS.output_folder_path / "downloading").iterdir():
        if file.is_file():
            file.unlink()

    # TODO start worker that queues jobs, sorted by (channel, -message_id)
    # TODO start workers that grab updated messages from telegram and cache
    # TODO start workers that download, convert and finish job
    # TODO start worker that logs progress

    with (
        # ThreadPoolExecutor(max_workers=1) as worker_queue_jobs,
        ThreadPoolExecutor(max_workers=1) as worker_update_telegram_messages,
        ThreadPoolExecutor(max_workers=SECRETS.parallel_downloads_count) as worker_downloader,
        ThreadPoolExecutor(max_workers=1) as _worker_parse_channels,
        ThreadPoolExecutor(max_workers=1) as worker_log_progress,
    ):
        futures = []
        futures.append(worker_update_telegram_messages.submit(DownloadWorker.update_telegram_messages))

        futures.append(worker_log_progress.submit(status_update))

        for i in range(SECRETS.parallel_downloads_count):
            futures.append(worker_downloader.submit(DownloadWorker.downloader, i + 1))

        def handle_exception(future):
            try:
                _data = future.result()
            except SystemExit:
                raise
            except:  # noqa: E722
                sys.exit(1)

        for future in as_completed(futures):
            future.add_done_callback(handle_exception)

    # DownloadWorker.update_telegram_messages()

    # await DownloadWorker.launch_workers(n=SECRETS.parallel_downloads_count)

    # # Start parsing channels and messages
    # await parse_channel_messages()


if __name__ == "__main__":
    current_folder = Path(__file__).parent.parent
    main()
