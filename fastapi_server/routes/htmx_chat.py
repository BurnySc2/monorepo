# pyre-ignore-all-errors
from __future__ import annotations

import os
from typing import Annotated

from litestar import Controller, get
from litestar.params import Parameter
from litestar.response import Template

from routes.login_logout import COOKIES

# connected_users: OrderedDict[str, list[WebSocket]] = OrderedDict()
# user_is_typing: OrderedDict[str, str] = OrderedDict()

# BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")


class MyChatRoute(Controller):
    path = "/chat"

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(
            template_name="chat/index.html",
        )

    @get("/htmxapi/chatheader")
    async def api_chat_header(
        self, github_access_token: Annotated[str | None, Parameter(cookie=COOKIES["github"])]
    ) -> Template:
        return Template(
            template_name="chat/chat_header.html",
            context={
                "client_id": CLIENT_ID,
                "logged_in": github_access_token is not None,
            },
        )


# async def get_username(
#     github_access_token: Annotated[str | None, Cookie()] = None,
# ) -> str | None:
#     if github_access_token is None:
#         return None
#     async with aiohttp.ClientSession() as session:
#         get_response = await session.get(
#             "https://api.github.com/user",
#             headers={"Authorization": f"Bearer {github_access_token}"},
#         )
#         if not get_response.ok:
#             return "error etc"
#         data = await get_response.json()
#         return data["login"]


# async def broadcast(message: str) -> None:
#     for websocket_list in connected_users.values():
#         for websocket in websocket_list:
#             await websocket.send_text(message)


# async def handle_join(user: str, websocket: WebSocket) -> None:
#     await websocket.accept()
#     # Clear chat messages
#     await websocket.send_text(
#         """
#     <div hx-swap-oob="innerHTML:#content" />
#     """
#     )
#     # Clear user list
#     await websocket.send_text(
#         """
#     <div hx-swap-oob="innerHTML:#userlist" />
#     """
#     )

#     # Send message history
#     messages = await get_all_messages()
#     rendered_messages = render(
#         templates,
#         "chat_message.html",
#         [
#             {
#                 "time_stamp": c.get("time_stamp"),
#                 "message_author": c.get("message_author"),
#                 "chat_message": c.get("chat_message"),
#             }
#             for c in messages
#         ],
#     )
#     await websocket.send_text(rendered_messages)

#     # Send user list
#     t = templates.get_template("chat_user.html")
#     await websocket.send_text(
#         "".join(
#             t.render(
#                 {
#                     "username": u,
#                 }
#             )
#             for u in connected_users
#         )
#     )
#     # Nofity all connected that someone joined
#     if user in connected_users:
#         connected_users[user].append(websocket)
#     else:
#         connected_users[user] = [websocket]
#     await broadcast(
#         t.render(
#             {
#                 "username": user,
#             }
#         )
#     )


# async def handle_leave(user: str, websocket: WebSocket) -> None:
#     if user not in connected_users:
#         logger.error("Received websocket disconnect from unknown user")
#         return
#     if websocket not in connected_users[user]:
#         logger.error("Received websocket disconnect from unknown websocket")
#         return
#     connected_users[user].remove(websocket)
#     if len(connected_users[user]) == 0:
#         del connected_users[user]
#     # TODO notify other users that user has disconnected, how to realize it in htmx?
#     # for u, w in connected_users.items():
#     #     await w.send_text(t.render({
#     #         "username": u,
#     #     }))


# async def handle_message(user: str, message: str, websocket: WebSocket) -> None:
#     new_message = await add_message(
#         arrow.now().format("HH:mm:ss"),
#         user,
#         message,
#     )

#     t = templates.get_template("chat_message.html")
#     # TODO Scroll to bottom of chat https://css-tricks.com/books/greatest-css-tricks/pin-scrolling-to-bottom/
#     await broadcast(
#         t.render(
#             {
#                 "time_stamp": new_message.get("time_stamp"),
#                 "message_author": new_message.get("message_author"),
#                 "chat_message": new_message.get("chat_message"),
#             }
#         )
#     )


# async def handle_typing(user: str, message: str, websocket: WebSocket) -> None:
#     # TODO dont show typing for yourself
#     if user not in user_is_typing:
#         user_is_typing[user] = message
#         await broadcast(
#             f"""
# <div hx-swap-oob="beforeend:#typing">
#     <div id="typing_{user}" />
# </div>
# """
#         )
#     if message == "":
#         # Delete 'user is typing'
#         if user in user_is_typing:
#             del user_is_typing[user]
#             await broadcast(
#                 f"""
#         <div hx-swap-oob="delete:#typing_{user}" />"""
#             )
#         return
#     t = templates.get_template("chat_typing.html")
#     await broadcast(
#         t.render(
#             {
#                 "message_author": user,
#                 "chat_message": message,
#             }
#         )
#     )


# @htmx_chat_router.websocket("/htmx_ws")
# async def htmx_chat_websocket(
#     websocket: WebSocket,
#     user: Annotated[str | None, Depends(get_username)],
# ):
#     logger.info("Received websocket connection")
#     if user is None:
#         logger.info("Declined websocket connection because of missing cookie")
#         return

#     await handle_join(user, websocket)

#     while 1:
#         try:
#             data = await websocket.receive_json()
#         except WebSocketDisconnect:
#             # User disconnected
#             await handle_leave(user, websocket)
#             return

#         # TODO Update message list on DELETE

#         # TODO Check for HEADERS['HX-Trigger-Name']
#         # TODO react to key-up events and send content to all users (except to the one who is typing)
#         if "chat_message" in data and data["HEADERS"]["HX-Trigger-Name"] == "chat_message_form":
#             # User sent a message
#             await handle_message(user, data["chat_message"], websocket)
#             # TODO Reset typing field
#             # Reset input field
#             t = templates.get_template("chat_input.html")
#             await websocket.send_text(t.render({}))
#             # User stopped typing
#             await handle_typing(user, "", websocket)
#         if "chat_message" in data and data["HEADERS"]["HX-Trigger-Name"] == "chat_message":
#             # User is typing
#             await handle_typing(user, data["chat_message"], websocket)


# # TODO Only expose route in DEV stage
# @htmx_chat_router.delete("/htmxapi/detele_messages", response_class=HTMLResponse)
# async def debug_delete_messages(
#     user: Annotated[str | None, Depends(get_username)],
# ):
#     if user is None:
#         return
#     await debug_delete_all_messages()
