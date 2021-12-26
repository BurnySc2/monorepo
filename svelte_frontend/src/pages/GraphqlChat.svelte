<script lang="ts">
    import { onDestroy } from "svelte"
    import moment from "moment"
    import { request, gql } from "graphql-request"
    import { subscribe } from "../functions/subscriptions"

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

    const ip = process.env.BACKEND_SERVER || "localhost:8000"
    const GRAPHQL_ENDPOINT = `http://${ip}/graphql`
    const GRAPHQL_WS_ENDPOINT = `ws://${ip}/graphql`

    // Active users in the room
    let activeChatters: string[] = []
    // Default message
    let messages: Message[] = [{ timestamp: 123, author: "yolo", message: "example message" }]

    let unsubscribeUserJoinedEvent: () => void
    let unsubscribeUserLeftEvent: () => void
    let unsubscribeNewMessageEvent: () => void

    onDestroy(async () => {
        disconnect()
    })

    const connect = async () => {
        // Send username selection
        const joinChatroomMutation = gql`
            mutation {
                chatJoinRoom(username: "${selectedUserName}")
            }
        `
        const joinChatroomResponse = await request(GRAPHQL_ENDPOINT, joinChatroomMutation)

        if (joinChatroomResponse.chatJoinRoom) {
            userName = selectedUserName
            errorMessage = ""
        } else {
            errorMessage = `Username ${selectedUserName} is already taken!`
            return
        }
        // Get all active chatters
        const getChattersQuery = gql`
            {
                chatUsers
            }
        `
        const activeChattersResponse = await request(GRAPHQL_ENDPOINT, getChattersQuery)
        activeChatters = activeChattersResponse.chatUsers

        // Get all previous messages
        const getMessagesQuery = gql`
            {
                chatMessages {
                    timestamp
                    author
                    message
                }
            }
        `
        const allMessagesResponse = await request(GRAPHQL_ENDPOINT, getMessagesQuery)
        messages = allMessagesResponse.chatMessages
        // Subscribe to new events
        unsubscribeUserJoinedEvent = subscribe(
            GRAPHQL_WS_ENDPOINT,
            gql`
                subscription {
                    chatUserJoined {
                        data
                    }
                }
            `,
            userJoinedEvent
        )
        unsubscribeUserLeftEvent = subscribe(
            GRAPHQL_WS_ENDPOINT,
            gql`
                subscription {
                    chatUserLeft {
                        data
                    }
                }
            `,
            userLeftEvent
        )
        unsubscribeNewMessageEvent = subscribe(
            GRAPHQL_WS_ENDPOINT,
            gql`
                subscription {
                    chatNewMessage {
                        timestamp
                        author
                        message
                    }
                }
            `,
            newMessageEvent
        )
    }

    const disconnect = async () => {
        unsubscribeUserJoinedEvent()
        unsubscribeUserLeftEvent()
        unsubscribeNewMessageEvent()
        const disconnectMutation = gql`
        mutation {
            chatLeaveRoom (username: "${userName}")
        }
        `
        await request(GRAPHQL_ENDPOINT, disconnectMutation)
        userName = ""
    }

    const userJoinedEvent = (subscriptionResponse: any) => {
        console.log(subscriptionResponse)
        const username: string = subscriptionResponse.data.chatUserJoined
        activeChatters = [...activeChatters, username]
        // TODO show active chatters list in chatroom
    }
    const userLeftEvent = (subscriptionResponse: any) => {
        console.log(subscriptionResponse)
        const username: string = subscriptionResponse.data.chatUserLeft
        activeChatters = activeChatters.filter((item) => item !== username)
    }
    const newMessageEvent = (subscriptionResponse: any) => {
        console.log(subscriptionResponse)
        const message: Message = subscriptionResponse.data.chatNewMessage
        messages = [...messages, message]
    }

    const handleKeydown = async (e: KeyboardEvent) => {
        // Or use e.code: "NumpadEnter or "Enter" for more specific handling
        if (e.key === "Enter") {
            await sendChatMessage()
        }
    }

    const sendChatMessage = async () => {
        const sendChatMessageMutation = gql`
            mutation {
                chatSendMessage (username: "${userName}", message: "${chatMessage}")
            }
        `
        chatMessage = ""
        await request(GRAPHQL_ENDPOINT, sendChatMessageMutation)
    }
</script>

{#if userName === ""}
    <!-- Before connection -->
    <div class="flex flex-column m2 rounded items-center">
        <div>Connect to graphql chat</div>
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
        <button id="connect" on:click={connect} class="rounded p1">Connect</button>
        <div>{errorMessage}</div>
    </div>
{:else}
    <!-- Connected -->
    <div class="flex flex-column">
        <button on:click={disconnect}>Leave chatroom</button>
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
            <input
                id="chatinput"
                class="col-span-9"
                type="text"
                on:keydown={handleKeydown}
                bind:value={chatMessage}
                placeholder={`Write your message as '${userName}'`}
            />
            <button id="sendmessage" class="col-span-1" on:click={sendChatMessage}>Send</button>
        </div>
    </div>
{/if}
