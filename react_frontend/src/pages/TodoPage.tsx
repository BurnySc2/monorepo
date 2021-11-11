import React, { useEffect, useState } from "react"
import TodoItem from "../components/TodoItem"
import { delete_, get, post } from "../functions/fetch_helper"

type ITodoItem = {
    id: number
    content: string
}

export default function TodoPage(): JSX.Element {
    const [newTodoText, setNewTodoText] = useState("")
    const [todos, setTodos] = useState<ITodoItem[]>([])
    const [APIserverIsResponding, setAPIserverIsResponding] = useState(true)

    useEffect(() => {
        getTodos()
    }, [])

    const getTodos = async () => {
        try {
            const response = await get("/api")
            if (response.ok) {
                setTodos(await response.json())
                setAPIserverIsResponding(true)
                // console.log(`Response is: ${JSON.stringify(cards)}`);
            } else {
                throw new Error(response.statusText)
            }
        } catch {
            setAPIserverIsResponding(false)
        }
    }

    const submitPressed = async () => {
        /*
        To add optional search params, use:
        let params = new URLSearchParams("")
        params.set("mykey", "myvalue")
        fetch(`/api/${newTodo}?` + params.toString(), requestOptions)
         */
        if (APIserverIsResponding) {
            await post(`/api/${newTodoText}`)
        } else {
            localSubmit()
        }
        setNewTodoText("")
        await getTodos()
    }

    const submitPressedBody = async () => {
        if (APIserverIsResponding) {
            await post("/api_body", {
                new_todo: newTodoText,
            })
        } else {
            localSubmit()
        }
        setNewTodoText("")
        await getTodos()
    }

    const submitPressedModel = async () => {
        if (APIserverIsResponding) {
            const response = await post("/api_model", {
                todo_description: newTodoText,
            })
            if (!response.ok) {
                // If error, then you can debug here and see which fields were missing/expected
                const body = await response.text()
                console.log(body)
            }
        } else {
            localSubmit()
        }
        setNewTodoText("")
        await getTodos()
    }

    const removeTodo = async (id: number) => {
        if (APIserverIsResponding) {
            await delete_(`/api/${id}`)
        } else {
            localRemove(id)
        }
        await getTodos()
    }

    const localSubmit = () => {
        // Add an item to local todolist
        let maxIndex = 0
        todos.forEach((todo) => {
            maxIndex = Math.max(todo.id, maxIndex)
        })
        setTodos([...todos, { id: maxIndex + 1, content: newTodoText }])
        setNewTodoText("")
    }

    const localRemove = (id: number) => {
        // Remove an item from local todolist
        const index = todos.findIndex((obj) => {
            return obj.id === id
        })
        if (index >= 0) {
            setTodos([...todos.slice(undefined, index), ...todos.slice(index + 1)])
        }
    }

    // Render UI
    const todoTextInput = (
        <input
            id="newTodoInput"
            className="border-2 my-2 mx-1"
            type="text"
            onChange={(e) => {
                setNewTodoText(e.target.value)
            }}
            value={newTodoText}
            placeholder="My new todo item"
        />
    )

    const renderTodoItem = (todoItem: ITodoItem, index: number) => {
        return (
            <TodoItem
                index={index}
                id={todoItem.id}
                content={todoItem.content}
                deleteFunction={() => removeTodo(todoItem.id)}
                key={todoItem.id}
            />
        )
    }

    const renderApiServerResponding = APIserverIsResponding ? (
        ""
    ) : (
        <div className="bg-red-300 rounded p-1">Unable to connect to server - running local mode</div>
    )

    return (
        <div>
            <div className="flex flex-col items-center">
                <div className="flex">
                    {todoTextInput}
                    <button className="border-2 my-2 mx-1" id="submit1" onClick={submitPressed}>
                        Submit
                    </button>
                    <button className="border-2 my-2 mx-1" id="submit2" onClick={submitPressedBody}>
                        SubmitBody
                    </button>

                    <button className="border-2 my-2 mx-1" id="submit3" onClick={submitPressedModel}>
                        SubmitModel
                    </button>
                </div>
                {renderApiServerResponding}
            </div>

            <div className="grid grid-cols-1 justify-items-center ">
                <div>{todos.map(renderTodoItem)}</div>
            </div>
        </div>
    )
}
