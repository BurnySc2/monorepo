# from __future__ import annotations

# from dataclasses import dataclass
# from typing import Annotated

# from litestar import Controller, get, patch, post
# from litestar.contrib.jinja import JinjaTemplateEngine
# from litestar.enums import RequestEncodingType
# from litestar.params import Body
# from litestar.response import Template
# from litestar.template.config import TemplateConfig

# from models.todo_item import add_todo, delete_todo, get_all_todos, toggle_todo

# template_config = TemplateConfig(engine=JinjaTemplateEngine, directory="templates")


# @dataclass
# class NewTodoItem:
#     todo_text: str


# class MyTodoRoute(Controller):
#     path = "/todo"

#     @get("/")
#     async def index(self) -> Template:
#         return Template(template_name="todo/index.html", context={})

#     @get("/api")
#     async def get_todos(self) -> Template:
#         todos = await get_all_todos()
#         return Template(
#             template_name="todo/todo_items.html",
#             context={
#                 "items": [
#                     {
#                         "id": c.get("id"),
#                         "todotext": c.get("todotext"),
#                         "done": c.get("done"),
#                     }
#                     for c in todos
#                 ]
#             },
#         )

#     @post("/api")
#     async def add_todo_item(
#         self,
#         data: Annotated[NewTodoItem, Body(media_type=RequestEncodingType.URL_ENCODED)],
#     ) -> Template:
#         row = await add_todo(data.todo_text)
#         return Template(
#             template_name="todo/todo_items.html",
#             context={
#                 "items": [
#                     {
#                         "id": row.get("id"),
#                         "todotext": row.get("todotext"),
#                         "done": row.get("done"),
#                     }
#                 ]
#             },
#         )

#     @patch("/api/{todoid: int}")
#     async def update_todo_item(self, todoid: int) -> None:
#         # TODO Replace todo item instead
#         await toggle_todo(todoid)

#     @post("/delete/{todoid: int}")
#     async def del_todo_item(self, todoid: int) -> str:
#         """
#         Replace the element to make sure that the request went through, instead of using 'hx-swap="delete"'.
#         """
#         await delete_todo(todoid)
#         return ""
