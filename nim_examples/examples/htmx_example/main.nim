import prologue
import mustache
import prologue/middlewares/cors

import tables
import strutils
import sequtils
import locks
import uri

import ./backend/todo_item

# Mark 'todos' to be guarded by this lock
var glock: Lock
var todos {.guard: glock.}: seq[TodoItem] = @[
    # (0, "hello world", false)
]

proc hello*(ctx: prologue.Context) {.async.} =
    resp readFile("templates/hello_world.html")

proc getTodos*(ctx: context.Context) {.async, gcsafe.} =
    var total: string
    let myTemplate = readFile("templates/todo_item.html")
    # Tell compiler to shut up
    # https://stackoverflow.com/a/76583939
    {.cast(gcsafe).}:
        # https://nim-lang.org/docs/manual.html#guards-and-locks-sections-protecting-global-variables
        withLock glock:
            for todo in todos:
                total &= myTemplate.render(newContext(values = {
                    "id": todo.id.castValue,
                    "text": todo.text.castValue,
                    "done": todo.done.castValue,
                }.toTable))
    resp total

proc addTodo*(ctx: context.Context) {.async, gcsafe.} =
    let data: Table[string, string] = ctx.request.body.decodeQuery.toSeq.toTable
    var newTodo: TodoItem
    {.cast(gcsafe).}:
        withLock glock:
            let todoTask = data["todo"]
            let todoId: int = if todos.len == 0: 0
                else: todos[^1].id + 1
            newTodo = (todoId, todoTask, false)
            todos.add(newTodo)
    resp readFile("templates/todo_item.html").render(newContext(values = {
                    "id": newTodo.id.castValue,
                    "text": newTodo.text.castValue,
                    "done": newTodo.done.castValue,
        }.toTable))

proc toggleTodo*(ctx: context.Context) {.async, gcsafe.} =
    let todoId = ctx.request.pathParams["todoId"].parseInt
    {.cast(gcsafe).}:
        withLock glock:
            # TODO Return error if todo item doesnt exist?
            for todo in todos.mitems:
                if todo.id == todoId:
                    todo.done = not todo.done
                    break

proc deleteTodo*(ctx: context.Context) {.async, gcsafe.} =
    let todoId = ctx.request.pathParams["todoId"].parseInt
    {.cast(gcsafe).}:
        withLock glock:
            # TODO Return error if todo item doesnt exist?
            todos = todos.filter(
                proc(todo: TodoItem): bool =
                return todo.id != todoId
            )

const urlPatterns = @[
    pattern("/", hello, @[HttpGet]),
    pattern("/todo", getTodos, @[HttpGet]),
    pattern("/todo", addTodo, @[HttpPost]),
    pattern("/todo/{todoId}", toggleTodo, @[HttpPatch]),
    pattern("/todo/{todoId}", deleteTodo, @[HttpDelete]),
]

# TODO Allow cors only for localhost when developing
let corsSettings = CorsMiddleware(allowOrigins = @["*"], allowHeaders = @["*"],
  allowMethods = @["*"], )

let settings = newSettings(port = Port(8080))
when isMainModule:
    let app = newApp(settings, @[corsSettings])
    app.addRoute(urlPatterns, "")
    app.run()
