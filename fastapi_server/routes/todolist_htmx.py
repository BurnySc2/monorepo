from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.routing import APIRouter
from fastapi.templating import Jinja2Templates

from models.todo_item import add_todo, delete_todo, get_all_todos, toggle_todo

htmx_todolist_router = APIRouter()
index_templates = Jinja2Templates(directory="frontend/todolist_htmx")
templates = Jinja2Templates(directory="templates")


# TODO disable endpoint in production as this should be served by a frontend separately
@htmx_todolist_router.get("/todo", response_class=HTMLResponse)
def todo_index(request: Request):
    return index_templates.TemplateResponse("index.html", {"request": request})


@htmx_todolist_router.get("/htmxapi/todo", response_class=HTMLResponse)
async def get_todo_items(request: Request):
    t = templates.get_template("todo_item.html")
    todos = await get_all_todos()
    return "".join(
        t.render({
            "request": request,
            "id": c.get("id"),
            "todotext": c.get("todotext"),
            "done": c.get("done"),
        }) for c in todos
    )


@htmx_todolist_router.post("/htmxapi/todo", response_class=HTMLResponse)
async def add_todo_item(request: Request, todotext: str = Form()):
    row = await add_todo(todotext)
    return templates.TemplateResponse(
        "todo_item.html", {
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
    await delete_todo(todoid)
    return ""
