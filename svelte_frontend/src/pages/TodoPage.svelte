<script lang="ts">
    import { onMount } from "svelte"
    import TodoCard from "../components/TodoCard.svelte"

    let newTodoText = ""
    let cards: { id: number; todo_text: string; created_timestamp: number; done_timestamp: number; done: boolean }[] = [
        { id: 0, todo_text: "some todo text", created_timestamp: 123, done_timestamp: -1, done: false },
    ]
    let APIserverIsResponding = true

    const ip = process.env.BACKEND_SERVER || "localhost:8000"
    const api_server_ip = `http://${ip}`

    onMount(async () => {
        // console.log("Loading todos")
        await getTodos()
    })

    const localSubmit = () => {
        // Add an item if server isnt responding
        let maxIndex = 0
        cards.forEach((card) => {
            maxIndex = Math.max(card.id, maxIndex)
        })
        maxIndex += 1
        cards = [...cards, { id: maxIndex, todo_text: newTodoText }]
    }

    const localRemove = (id: number) => {
        // Remove an item if server isnt responding
        let obj = cards.find((obj) => {
            return obj.id === id
        })
        if (obj) {
            let index = cards.indexOf(obj)
            if (index >= 0) {
                cards = [...cards.slice(undefined, index), ...cards.slice(index + 1)]
            }
        }
    }

    const getTodos = async () => {
        APIserverIsResponding = true
        try {
            let response = await fetch(`${api_server_ip}/api`)
            if (response.ok) {
                cards = await response.json()
                // console.log(`Response is: ${JSON.stringify(cards)}`);
            } else {
                throw new Error(response.statusText)
            }
        } catch {
            APIserverIsResponding = false
        }
    }

    const submitPressed = async () => {
        /*
        To add optional search params, use:
        let params = new URLSearchParams("")
        params.set("mykey", "myvalue")
        fetch(`/api/${newTodo}?` + params.toString(), requestOptions)
         */
        try {
            await fetch(`${api_server_ip}/api/${newTodoText}`, {
                method: "POST",
            })
        } catch {
            localSubmit()
        }
        newTodoText = ""
        await getTodos()
    }

    const submitPressedBody = async () => {
        // When using request body:
        try {
            const requestOptions = {
                method: "POST",
                body: JSON.stringify({
                    new_todo: newTodoText,
                }),
            }
            await fetch(`${api_server_ip}/api_body`, requestOptions)
        } catch {
            localSubmit()
        }
        newTodoText = ""
        await getTodos()
    }

    const submitPressedModel = async () => {
        // When using request body:
        try {
            const requestOptions = {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    todo_description: newTodoText,
                }),
            }
            await fetch(`${api_server_ip}/api_model`, requestOptions)
        } catch {
            localSubmit()
        }
        newTodoText = ""
        await getTodos()
    }

    const removeTodo = async (id: number) => {
        try {
            await fetch(`${api_server_ip}/api/${id}`, {
                method: "DELETE",
            })
        } catch {
            localRemove(id)
        }
        await getTodos()
    }
</script>

<main class="flex flex-col items-center">
    <div class="flex">
        <input
            id="newTodoInput"
            class="border-2 my-2 mx-1"
            type="text"
            bind:value={newTodoText}
            placeholder="My new todo item"
        />
        <button class="border-2 my-2 mx-1" id="submit1" on:click={submitPressed}>Submit</button>
        <button class="border-2 my-2 mx-1" id="submit2" on:click={submitPressedBody}>SubmitBody</button>
        <button class="border-2 my-2 mx-1" id="submit3" on:click={submitPressedModel}>SubmitModel</button>
    </div>
    {#if !APIserverIsResponding}
        <div class="bg-red-300 border-2 p-1">Unable to connect to server - running local mode</div>
    {/if}
    {#each cards as { id, todo_text }, _i}
        <TodoCard cardText={todo_text} index={id} {removeTodo} />
    {/each}
    <!-- Same as above -->
    <!-- {#each cards as card, i}
        <TodoCard cardText={card.todo_text} index={card.id} {removeTodo} />
    {/each} -->
</main>
