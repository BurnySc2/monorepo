<script lang="ts">
    import { onDestroy, onMount } from "svelte"
    import moment from "moment"

    let componentMounted = false

    // Accepted username by server
    let userName = ""
    // Username in the "your username" input field
    let selectedUserName = ""
    // When sending the username to server, do not allow client to send new requests (this field will be filled with the username)
    let waitingForUserNameResponse = ""

    let chatMessage = ""

    let errorMessage = ""

    type Message = {
        timestamp: number
        author: string
        message: string
    }
    // Default message
    let messages: Message[] = [{ timestamp: 123, author: "yolo", message: "example message" }]

    let ws: WebSocket | null = null
    const ip = process.env.BACKEND_SERVER || "localhost:8000"
    const connect = () => {
        ws = new WebSocket(`ws://${ip}/chatws`)

        ws.onmessage = (event) => {
            // Called when message received
            try {
                const content = JSON.parse(event.data)
                console.log("Received:")
                console.log(JSON.stringify(content))

                if ("message" in content) {
                    // Received example message
                    console.log(`Received: ${content.message}`)
                } else if ("error" in content) {
                    // Error handling
                    if (content.error === "usernameTaken") {
                        errorMessage = `Username '${waitingForUserNameResponse}' is already taken!`
                        waitingForUserNameResponse = ""
                    }
                } else if ("newMessage" in content) {
                    // Received new message
                    console.log(`Received new message: ${JSON.stringify(content.newMessage)}`)

                    messages = [...messages, content.newMessage]
                } else if ("newMessageHistory" in content) {
                    // Received new message
                    console.log(`Received new message history: ${content.newMessage}`)

                    messages = [...messages, ...content.newMessageHistory]
                } else if ("connectUser" in content) {
                    // User connected, server accepted the username
                    console.log(`Successfully connected to server with username ${content.connectUser}`)
                    errorMessage = ""
                    waitingForUserNameResponse = ""
                    userName = content.connectUser
                }
            } catch {
                // Message was not in JSON format
                console.log("Received unreadable data!")
                console.log(JSON.stringify(event.data))
            }
        }

        ws.onclose = () => {
            // Called when connection is closed - e.g. when there was an error, when server shut down, or internet connection ended
            const sleepInSeconds = 5
            setTimeout(() => {
                if (componentMounted) {
                    connect()
                }
            }, sleepInSeconds * 1000)
        }

        ws.onopen = () => {
            if (ws) {
                const message = JSON.stringify({ message: "Hello from client!" })
                ws.send(message)
            }
        }

        ws.onerror = () => {
            if (ws) {
                ws.close()
            }
        }
    }

    onMount(async () => {
        componentMounted = true
        // On page load: connect to websocket
        connect()
    })

    onDestroy(async () => {
        componentMounted = false
    })

    const tryToConnectUser = async () => {
        // Send a username to the server and see if it is available
        errorMessage = ""
        if (ws && ws.readyState === 1) {
            console.log(`Trying to connect user ${selectedUserName}`)
            if (waitingForUserNameResponse === "") {
                waitingForUserNameResponse = selectedUserName
                ws.send(
                    JSON.stringify({
                        tryToConnectUser: selectedUserName,
                    })
                )
            }
        } else {
            errorMessage = "WebSocket is not yet ready!"
        }
    }

    const handleKeydown = async (e: KeyboardEvent) => {
        // Or use e.code: "NumpadEnter or "Enter" for more specific handling
        if (e.key === "Enter") {
            await sendChatMessage()
        }
    }

    const sendChatMessage = async () => {
        if (chatMessage !== "") {
            if (ws && ws.readyState === 1) {
                if (userName !== "") {
                    ws.send(
                        JSON.stringify({
                            sendChatMessage: {
                                timestamp: Date.now() / 1000,
                                author: userName,
                                message: chatMessage,
                            },
                        })
                    )
                    chatMessage = ""
                }
            } else {
                console.log("Unable to send message - WS not yet ready")
            }
        }
    }
</script>

{#if userName === ""}
    <!-- Before connection -->
    <div class="flex flex-col m-2 border-2 items-center">
        <div>Connect to chat</div>
        {#if waitingForUserNameResponse === ""}
            <input id="username" type="text" placeholder="Username" class="border-2" bind:value={selectedUserName} />
        {:else}
            <input
                type="text"
                placeholder="Username"
                class="border-2"
                readonly
                bind:value={waitingForUserNameResponse}
            />
        {/if}
        <button id="connect" on:click={tryToConnectUser} class="border-2 p-1">Connect</button>
        <div>{errorMessage}</div>
    </div>
{:else}
    <!-- Connected -->
    <div class="flex flex-col">
        <div id="Chat box" class="grid grid-cols-10 overflow-y-auto">
            <!-- Messages sent by everyone -->
            {#each messages as message}
                <div class="col-span-1">
                    {moment(message.timestamp * 1000).format("HH:mm:ss")}
                </div>
                <!-- <div class="col-span-1">{moment(message.timestamp*1000).format("LTS")}</div> -->
                {#if message.author === userName}
                    <div class="col-span-1">You</div>
                {:else}
                    <div class="col-span-1">{message.author}</div>
                {/if}
                <div class="col-span-8">{message.message}</div>
            {/each}
        </div>
        <div class="grid grid-cols-10">
            <input id="chatinput" class="col-span-9" type="text" on:keydown={handleKeydown} bind:value={chatMessage} />
            <button id="sendmessage" class="col-span-1" on:click={sendChatMessage}>Send</button>
        </div>
    </div>
{/if}
