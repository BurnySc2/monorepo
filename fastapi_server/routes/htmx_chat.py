import os
from collections import OrderedDict
from typing import Annotated

import aiohttp
import arrow
from fastapi import (
    Cookie,
    Depends,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates
from loguru import logger

from models.chat_messages import add_message, get_all_messages

htmx_chat_router = APIRouter()
index_templates = Jinja2Templates(directory="frontend/chat")
templates = Jinja2Templates(directory="templates/chat")

connected_users: OrderedDict[str, list[WebSocket]] = OrderedDict()

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")


# TODO disable endpoint in production as this should be served by a frontend separately
@htmx_chat_router.get("/chat", response_class=HTMLResponse)
def chat_index(request: Request):
    return index_templates.TemplateResponse("index.html", {"request": request, "server_url": BACKEND_SERVER_URL})


async def get_username(github_access_token: Annotated[str | None, Cookie()] = None, ) -> str | None:
    if github_access_token is None:
        return None
    async with aiohttp.ClientSession() as session:
        get_response = await session.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_access_token}"},
        )
        if not get_response.ok:
            return "error etc"
        data = await get_response.json()
        return data["login"]


async def broadcast(message: str) -> None:
    for websocket_list in connected_users.values():
        for websocket in websocket_list:
            await websocket.send_text(message)


async def handle_join(user: str, websocket: WebSocket) -> None:
    await websocket.accept()

    # Send message history
    messages = await get_all_messages()
    t = templates.get_template("chat_message.html")
    rendered_messages = "".join(
        t.render(
            {
                "time_stamp": c.get("time_stamp"),
                "message_author": c.get("message_author"),
                "chat_message": c.get("chat_message"),
            }
        ) for c in reversed(messages)
    )
    await websocket.send_text(rendered_messages)

    # Send user list
    t = templates.get_template("chat_user.html")
    await websocket.send_text("".join(t.render({
        "username": u,
    }) for u in connected_users))
    # Nofity all connected that someone joined
    if user in connected_users:
        connected_users[user].append(websocket)
    else:
        connected_users[user] = [websocket]
    await broadcast(t.render({
        "username": user,
    }))


async def handle_leave(user: str, websocket: WebSocket) -> None:
    if user not in connected_users:
        logger.error("Received websocket disconnect from unknown user")
        return
    if websocket not in connected_users[user]:
        logger.error("Received websocket disconnect from unknown websocket")
        return
    connected_users[user].remove(websocket)
    if len(connected_users[user]) == 0:
        del connected_users[user]
    # TODO notify other users that user has disconnected, how to realize it in htmx?
    # for u, w in connected_users.items():
    #     await w.send_text(t.render({
    #         "username": u,
    #     }))


async def handle_message(user: str, message: str) -> None:
    new_message = await add_message(
        arrow.now().format("HH:mm:ss"),
        user,
        message,
    )

    t = templates.get_template("chat_message.html")
    logger.info(f"Received data: {message}")
    await broadcast(
        t.render(
            {
                "time_stamp": new_message.get("time_stamp"),
                "message_author": new_message.get("message_author"),
                "chat_message": new_message.get("chat_message"),
            }
        )
    )


@htmx_chat_router.get("/htmxapi/chatheader", response_class=HTMLResponse)
async def get_header(request: Request, github_access_token: Annotated[str | None, Cookie()] = None):
    return templates.TemplateResponse(
        "chat_header.html", {
            "request": request,
            "server_url": BACKEND_SERVER_URL,
            "client_id": CLIENT_ID,
            "logged_in": github_access_token is not None,
        }
    )


@htmx_chat_router.websocket("/htmx_ws")
async def htmx_chat_websocket(
    websocket: WebSocket,
    user: Annotated[str | None, Depends(get_username)],
):
    logger.info("Received websocket connection")
    if user is None:
        logger.info("Declined websocket connection because of missing cookie")
        return

    await handle_join(user, websocket)

    while 1:
        try:
            data = await websocket.receive_json()
        except WebSocketDisconnect:
            # User disconnected
            await handle_leave(user, websocket)
            return

        # TODO Update message list on DELETE

        if "chat_message" in data:
            # User sent a message
            await handle_message(user, data["chat_message"])
