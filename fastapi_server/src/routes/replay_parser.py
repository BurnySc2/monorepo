from hashlib import md5
from io import BytesIO

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from components.replay_pack_builder.models import ParsedReplayFile
from components.replay_pack_builder.replay_parser import parse_replay

replay_parser_router = APIRouter()


@replay_parser_router.post("/parse_replay")
async def parse_replay_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Parse a StarCraft II replay file and return the parsed data as JSON.

    The frontend handles all filtering, renaming, and zipping locally.
    """
    try:
        contents = await file.read()
        file_md5 = md5(contents).hexdigest()
        replay_data: ParsedReplayFile = await parse_replay(BytesIO(contents), file_md5)
        return JSONResponse(replay_data.model_dump())
    except Exception as e:  # noqa: BLE001
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )
