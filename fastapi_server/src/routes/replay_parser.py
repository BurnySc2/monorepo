from hashlib import md5
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile

from components.replay_pack_builder.models import ParsedReplayFile
from components.replay_pack_builder.replay_parser import parse_replay

replay_parser_router = APIRouter()


@replay_parser_router.post("/parse_replay", response_model=ParsedReplayFile)
async def parse_replay_file(file: UploadFile = File(...)) -> ParsedReplayFile:
    """
    Parse a StarCraft II replay file and return the parsed data as JSON.

    The frontend handles all filtering, renaming, and zipping locally.
    """
    try:
        contents = await file.read()
        file_md5 = md5(contents).hexdigest()
        replay_data: ParsedReplayFile = await parse_replay(BytesIO(contents), file_md5)
        return replay_data
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(e))
