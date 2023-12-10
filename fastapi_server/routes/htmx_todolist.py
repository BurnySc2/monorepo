from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates

from helper.jinja_renderer import render
from models.todo_item import add_todo, delete_todo, get_all_todos, toggle_todo

htmx_todolist_router = APIRouter()
index_templates = Jinja2Templates(directory="frontend/todo")
templates = Jinja2Templates(directory="templates/todo")


# TODO disable endpoint in production as this should be served by a frontend separately if login is not required
@htmx_todolist_router.get("/todo", response_class=HTMLResponse)
def todo_index(request: Request):
    return render(index_templates, "index.html", {"request": request})


@htmx_todolist_router.get("/htmxapi/todo", response_class=HTMLResponse)
async def get_todo_items(request: Request) -> str:
    todos = await get_all_todos()
    return render(
        templates, "todo_item.html", [
            {
                "request": request,
                "id": c.get("id"),
                "todotext": c.get("todotext"),
                "done": c.get("done"),
            } for c in todos
        ]
    )


@htmx_todolist_router.post("/htmxapi/todo", response_class=HTMLResponse)
async def add_todo_item(request: Request, todotext: str = Form()):
    row = await add_todo(todotext)
    return render(
        templates, "todo_item.html", {
            "request": request,
            "id": row.get("id"),
            "todotext": row.get("todotext"),
            "done": row.get("done"),
        }
    )


@htmx_todolist_router.patch("/htmxapi/todo/{todoid}")
async def update_todo_item(todoid: int):
    await toggle_todo(todoid)


@htmx_todolist_router.delete("/htmxapi/todo/{todoid}", response_class=HTMLResponse)
async def del_todo_item(todoid: int):
    """
    Replace the element to make sure that the request went through, instaed of using 'hx-swap="delete"'.
    """
    await delete_todo(todoid)
    return ""
