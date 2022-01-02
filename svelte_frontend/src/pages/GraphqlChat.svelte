<script lang="ts">
    import { onDestroy } from "svelte"
    import moment from "moment"
    import { gql } from "graphql-request"
    import { subscribe } from "../functions/subscriptions"
    import { GRAPHQL_CLIENT } from "../functions/constants"

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

        const joinChatroomResponse = await GRAPHQL_CLIENT.request(joinChatroomMutation)

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
        const activeChattersResponse = await GRAPHQL_CLIENT.request(getChattersQuery)
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
        const allMessagesResponse = await GRAPHQL_CLIENT.request(getMessagesQuery)
        messages = allMessagesResponse.chatMessages
        // Subscribe to new events
        unsubscribeUserJoinedEvent = subscribe(
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
        if (unsubscribeUserJoinedEvent) {
            unsubscribeUserJoinedEvent()
        }
        if (unsubscribeUserLeftEvent) {
            unsubscribeUserLeftEvent()
        }
        if (unsubscribeNewMessageEvent) {
            unsubscribeNewMessageEvent()
        }
        const disconnectMutation = gql`
        mutation {
            chatLeaveRoom (username: "${userName}")
        }
        `
        await GRAPHQL_CLIENT.request(disconnectMutation)
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
        await GRAPHQL_CLIENT.request(sendChatMessageMutation)
    }
</script>

{#if userName === ""}
    <!-- Before connection -->
    <div class="flex flex-col m-2 border-2 items-center">
        <div>Connect to graphql chat</div>
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
        <button id="connect" on:click={connect} class="border-2 p-1">Connect</button>
        <div>{errorMessage}</div>
    </div>
{:else}
    <!-- Connected -->
    <div class="flex flex-column">
        <button id="leavechatroom" on:click={disconnect}>Leave chatroom</button>
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
