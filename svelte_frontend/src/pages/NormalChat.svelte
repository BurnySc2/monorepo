<script lang="ts">
    import { onMount } from "svelte"
    import moment from "moment"

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
    const ip = "localhost:8000"
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
                } else if (content.hasOwnProperty("error")) {
                    // Error handling
                    if (content.error === "usernameTaken") {
                        errorMessage = `Username '${waitingForUserNameResponse}' is already taken!`
                        waitingForUserNameResponse = ""
                    }
                } else if ("newMessage" in content) {
                    // Received new message
                    console.log(`Received new message: ${JSON.stringify(content.newMessage)}`)

                    messages = [...messages, content.newMessage]
                } else if (content.hasOwnProperty("newMessageHistory")) {
                    // Received new message
                    console.log(`Received new message history: ${content.newMessage}`)

                    messages = [...messages, ...content.newMessageHistory]
                } else if (content.hasOwnProperty("connectUser")) {
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
            const sleep_in_seconds = 5
            setTimeout(() => {
                connect()
            }, sleep_in_seconds * 1000)
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
        // On page load: connect to websocket
        connect()
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
    <div class="flex flex-column m2 rounded items-center">
        <div>Connect to chat</div>
        {#if waitingForUserNameResponse === ""}
            <input id="username" type="text" placeholder="Username" class="rounded" bind:value={selectedUserName} />
        {:else}
            <input
                type="text"
                placeholder="Username"
                class="rounded"
                readonly
                bind:value={waitingForUserNameResponse}
            />
        {/if}
        <button id="connect" on:click={tryToConnectUser} class="rounded p1">Connect</button>
        <div>{errorMessage}</div>
    </div>
{:else}
    <!-- Connected -->
    <div class="flex flex-column">
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
