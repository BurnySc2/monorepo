import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from starlette.datastructures import QueryParams

from components.tts.irc_bot_async import IRCClient, ReadNameLang
from components.tts.websocket_handler import RoleFilter, TTSQueue, TTSQueueRunner
from components.tts_generate import list_all_voices

TTSRouter = APIRouter()

# Guard check-then-act creation of queue/runner/IRC bot against concurrent connects.
_tts_init_lock = asyncio.Lock()


def _parse_bool_param(v: str | None) -> bool:
    if v is None:
        return True
    return v.strip().lower() not in {"0", "false", "no", "off"}


def parse_role_filter(query: QueryParams) -> RoleFilter:
    return RoleFilter(
        allow_mods=_parse_bool_param(query.get("allow_mods")),
        allow_vips=_parse_bool_param(query.get("allow_vips")),
        allow_subs=_parse_bool_param(query.get("allow_subs")),
        allow_normal=_parse_bool_param(query.get("allow_normal")),
    )


@TTSRouter.websocket("/ws/{stream_name}/{read_name_lang}")
async def websocket_endpoint(websocket: WebSocket, stream_name: str, read_name_lang: ReadNameLang):
    """
    On new ws-connection:
        - join twitch channel
        - create worker that checks for new items in queue
    """
    # Cache tts voices to make them work
    await list_all_voices()

    await websocket.accept()

    role_filter = parse_role_filter(websocket.query_params)
    key = (stream_name, read_name_lang)
    async with _tts_init_lock:
        # Initialize text queue if not exists (setdefault guard + lock against race)
        if key not in TTSQueue.text_queue:
            TTSQueue.text_queue[key] = asyncio.Queue()
            # Create worker for this 'stream_name' and 'read_name_lang'.
            asyncio.create_task(
                TTSQueueRunner(stream_name, read_name_lang).run(),
                name=f"tts-runner-{stream_name}-{read_name_lang}",
            )

        # Add socket - needs to happen after text_queue is initialized
        TTSQueue.add_websocket(stream_name, read_name_lang, websocket, role_filter)

        # Start irc bot: listen to messages in channel
        if key not in TTSQueue.twitch_irc_bots:
            new_irc_client = IRCClient(
                channel=stream_name, read_name_lang=read_name_lang, callback=TTSQueue.irc_client_add_text_method
            )
            TTSQueue.twitch_irc_bots[key] = new_irc_client
            try:
                await new_irc_client.connect()
            except Exception as e:  # noqa: BLE001
                logger.exception(f"IRC connect failed for {stream_name}: {e}")
                # Drop half-initialized bot so a later connect can retry; keep queue/runner.
                TTSQueue.twitch_irc_bots.pop(key, None)
            else:
                # Keep irc bot running.
                asyncio.create_task(
                    new_irc_client.listen(),
                    name=f"irc-listen-{stream_name}-{read_name_lang}",
                )

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        await TTSQueue.remove_ws(websocket, stream_name, read_name_lang)
    except Exception as e:  # noqa: BLE001
        logger.exception(f"Unexpected error: {e}")
