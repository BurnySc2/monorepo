import prologue
import mustache
import prologue/middlewares/cors

import tables
import strformat
import sequtils
import locks

import ./backend/todo_item

# TODO todo-app with sqlite?
# CRUD endpoints

# Mark 'todos' to be guarded by this lock
var glock: Lock
var todos {.guard: glock.}: seq[TodoItem] = @[
    (1, "hello", false)
]

proc hello*(ctx: prologue.Context) {.async.} =
    resp readFile("templates/hello_world.html")

proc getTodos*(ctx: context.Context) {.async, gcsafe.} =
    var c = newContext()
    # Tell compiler to shut up
    # https://stackoverflow.com/a/76583939
    {.cast(gcsafe).}: 
        # https://nim-lang.org/docs/manual.html#guards-and-locks-sections-protecting-global-variables
        withLock glock:
            c["todos"] = todos
    resp readFile("templates/todo_list.html").render(c)

proc addTodo*(ctx: context.Context) {.async, gcsafe.} =
    resp readFile("templates/hello_world.html")

proc checkTodo*(ctx: context.Context) {.async, gcsafe.} =
    discard

proc uncheckTodo*(ctx: context.Context) {.async, gcsafe.} =
    discard

proc deleteTodo*(ctx: context.Context) {.async, gcsafe.} =
    discard

const urlPatterns = @[
    pattern("/", hello, @[HttpGet]),
    pattern("/todo", getTodos, @[HttpGet]),
    # pattern("/todo", addTodo, @[HttpPost]),
    # pattern("/todo", deleteTodo, @[HttpDelete]),
    # pattern("/todo", checkTodo, @[HttpPut]),
    # pattern("/todo", uncheckTodo, @[HttpPatch]),
]

# TODO Allow cors only for localhost when developing
let corsSettings = CorsMiddleware(allowOrigins = @["*"], allowHeaders = @["*"])

let settings = newSettings(port = Port(8080))
when isMainModule:
    let app = newApp(settings, @[corsSettings])

    app.addRoute(urlPatterns, "")
    app.run()
