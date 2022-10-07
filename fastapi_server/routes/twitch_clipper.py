from __future__ import annotations

import datetime
import os
import re
import subprocess
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse

clip_router = APIRouter()

DATA_FOLDER = Path(__file__).parents[1] / 'data'
DATA_FOLDER.mkdir(exist_ok=True)


@dataclass
class ClipInfo:
    total_match: str
    vod_id: str
    hours: str
    minutes: str
    seconds: str

    limit_in_kb: Optional[int] = None  # limit in kilobytes

    def __post_init__(self):
        self.hours = self.hours.zfill(2) if self.hours else '00'
        self.minutes = self.minutes.zfill(2) if self.minutes else '00'
        self.seconds = self.seconds.zfill(2) if self.seconds else '00'

    @classmethod
    def from_match(cls, match: re.Match) -> ClipInfo:
        return ClipInfo(
            match.group(0),
            match.group(1),
            match.group(2),
            match.group(3),
            match.group(4),
        )

    @property
    def url(self) -> str:
        return f'https://www.twitch.tv/videos/{self.vod_id}'

    @property
    def start_timestamp(self) -> str:
        return f'{self.hours}:{self.minutes}:{self.seconds}'

    @property
    def duration(self) -> datetime.timedelta:
        return datetime.timedelta(minutes=1)

    @property
    def download_path(self) -> Path:
        return DATA_FOLDER / f'{self.upload_name}_downloaded.mp4'

    @property
    def converted_path(self) -> Path:
        return DATA_FOLDER / f'{self.upload_name}_converted.mp4'

    @property
    def upload_name(self) -> str:
        return f'{self.vod_id}_{self.hours}_{self.minutes}_{self.seconds}'


def find_groups(url: str) -> ClipInfo:
    match = re.fullmatch(r'(\d+)\?t=(\d+)?h?(\d+)?m?(\d+)?s?', url)
    if not match:
        raise HTTPException(
            status_code=404, detail='Url does not match expected pattern. Expected pattern: dl_clip/vod_id?t=5h4m3s'
        )
    return ClipInfo.from_match(match)


def download_part_of_vod(clip_info: ClipInfo) -> None:
    quality = 'best'
    process = subprocess.Popen(
        [
            'streamlink',
            # "--hls-live-edge",
            # "6",
            # "--hls-segment-attempts",
            # "10",
            # "--hls-segment-threads",
            # "8",
            '--hls-start-offset',
            f'{clip_info.start_timestamp}',
            '--hls-duration',
            f'{clip_info.duration}',
            clip_info.url,
            quality,
            '-o',
            clip_info.download_path.absolute(),
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    process.wait()
    _debug = process.communicate()
    _debug = None


def convert_video_with_ffmpeg(clip_info: ClipInfo) -> None:
    if clip_info.limit_in_kb is None:
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-err_detect',
                'ignore_err',
                '-i',
                str(clip_info.download_path.absolute()),
                '-c',
                'copy',
                '-y',
                '-loglevel',
                'error',
                str(clip_info.converted_path.absolute()),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    else:
        target_kilobitrate: int = int(0.9 * 8 * clip_info.limit_in_kb // clip_info.duration.total_seconds())
        process = subprocess.Popen(
            [
                'ffmpeg',
                '-i',
                str(clip_info.download_path.absolute()),
                "-b",
                f"{target_kilobitrate}k",
                '-y',
                str(clip_info.converted_path.absolute()),
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
    process.wait()
    _debug = process.communicate()
    _debug = None


def download_clip_from_clip_info(clip_info: ClipInfo) -> BytesIO:
    download_part_of_vod(clip_info)
    convert_video_with_ffmpeg(clip_info)

    with clip_info.converted_path.open('rb') as f:
        data = f.read()
    data_rewinded = BytesIO(data)

    if clip_info.download_path.is_file():
        os.remove(clip_info.download_path)
    if clip_info.converted_path.is_file():
        os.remove(clip_info.converted_path)

    return data_rewinded


@clip_router.get('/dl_clip/{url}')
async def download_clip_from_vod(url: str, t: str):
    total_url = f'{url}?t={t}'
    clip_info: ClipInfo = find_groups(total_url)
    data = download_clip_from_clip_info(clip_info)

    return StreamingResponse(
        content=data, headers={
            'Content-Disposition': f'attachment;filename={clip_info.upload_name}.mp4',
        }
    )


@clip_router.get('/dl_clip_limit/{url}')
async def download_clip_from_vod_with_10mb_limit(url: str, t: str):
    total_url = f'{url}?t={t}'
    clip_info: ClipInfo = find_groups(total_url)
    clip_info.limit_in_kb = 8 * 2**10  # Limit clip to 10 mb
    data = download_clip_from_clip_info(clip_info)

    return StreamingResponse(
        content=data, headers={
            'Content-Disposition': f'attachment;filename={clip_info.upload_name}.mp4',
        }
    )
