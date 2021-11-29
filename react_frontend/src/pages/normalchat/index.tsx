import React, { KeyboardEvent, useEffect, useState } from "react"
import { Message, ChatMessage } from "../../components/ChatMessage"
import MyRouter from "../../components/MyRouter"

export default function NormalChat(): JSX.Element {
    // Accepted username by server
    const [userName, setUserName] = useState("")
    // Username in the "your username" input field
    const [selectedUserName, SetSelectedUserName] = useState("")
    // When sending the username to server, do not allow client to send new requests (this field will be filled with the username)
    const [waitingForUserNameResponse, setWaitingForUserNameResponse] = useState("")
    // The chat message the user is about to send
    const [chatMessage, setChatMessage] = useState("")
    const [errorMessage, setErrorMessage] = useState("")
    // All chat messages in the chat
    const [messages, setMessages] = useState<Message[]>([
        { timestamp: 123, author: "yolo", message: "example message" },
    ])

    useEffect(() => {
        connect()
    }, [])

    // Websocket connection handling
    const [ws, setws] = useState<WebSocket | null>(null)
    const connect = () => {
        const address = process.env.NEXT_PUBLIC_REACT_APP_WEBSOCKET
        if (!address) {
            console.error("process.env.REACT_APP_WEBSOCKET is not set! Check your Env variables")
        }
        const ws = new WebSocket(`${address}/chatws`)
        ws.onmessage = (event) => {
            // Called when message received
            try {
                const content = JSON.parse(event.data)
                console.log(`Received: ${Object.keys(content)}`)
                // console.log(JSON.stringify(content))
                if ("message" in content) {
                    // Received example message
                    console.log(`Received: ${content.message}`)
                } else if ("error" in content) {
                    // Error handling
                    if (content.error === "usernameTaken") {
                        setErrorMessage(`Username '${waitingForUserNameResponse}' is already taken!`)
                        setWaitingForUserNameResponse("")
                    }
                } else if ("newMessage" in content) {
                    // Received new message
                    // console.log(`Received new message: ${JSON.stringify(content.newMessage)}`)
                    // Why doesn't this work
                    // setMessages([...messages, content.newMessage])
                    setMessages((messages) => [...messages, content.newMessage])
                } else if ("newMessageHistory" in content) {
                    // Received new message
                    // console.log(`Received new message history: ${JSON.stringify(content.newMessageHistory)}`)
                    setMessages([...content.newMessageHistory])
                } else if ("connectUser" in content) {
                    // User connected, server accepted the username
                    console.log(`Successfully connected to server with username ${content.connectUser}`)
                    setErrorMessage("")
                    setWaitingForUserNameResponse("")
                    setMessages([])
                    setUserName(content.connectUser)
                }
            } catch {
                // Message was not in JSON format
                console.log("Received unreadable data!")
                console.log(event.data)
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
        setws(ws)
    }

    const tryToConnectUser = async () => {
        // Send a username to the server and see if it is available
        setErrorMessage("")
        if (ws && ws.readyState === 1) {
            console.log(`Trying to connect as user '${selectedUserName}'`)
            if (waitingForUserNameResponse === "") {
                setWaitingForUserNameResponse(selectedUserName)
                ws.send(
                    JSON.stringify({
                        tryToConnectUser: selectedUserName,
                    })
                )
            }
        } else {
            setErrorMessage("WebSocket is not yet ready!")
        }
    }

    const handleKeydown = async (e: KeyboardEvent<HTMLInputElement>) => {
        // Or use e.code: "NumpadEnter or "Enter" for more specific handling
        if (e.key === "Enter") {
            await sendChatMessage()
        }
    }

    const sendChatMessage = async () => {
        console.log("Trying to send chat message...")
        if (chatMessage !== "") {
            if (ws && ws.readyState === 1) {
                if (userName !== "") {
                    // TODO Once we send a message, we should receive a 'newMessage' within the next 2 seconds - disconnect (=set username to "") if none received
                    ws.send(
                        JSON.stringify({
                            sendChatMessage: {
                                timestamp: Date.now() / 1000,
                                author: userName,
                                message: chatMessage,
                            },
                        })
                    )
                    setChatMessage("")
                }
            } else {
                console.log("Unable to send message - WS not yet ready")
            }
        }
    }

    const rendered_messages = messages.map((message) => {
        const key = `${message.timestamp};${message.author};${message.message}`
        return <ChatMessage message={message} userName={userName} key={key} />
    })

    let userNameInputField: JSX.Element
    if (waitingForUserNameResponse === "") {
        userNameInputField = (
            <input
                id="username"
                type="text"
                placeholder="Username"
                className="border"
                value={selectedUserName}
                maxLength={20}
                onChange={(e) => {
                    SetSelectedUserName(e.target.value)
                }}
            />
        )
    } else {
        userNameInputField = (
            <input type="text" placeholder="Username" className="border" readOnly value={waitingForUserNameResponse} />
        )
    }

    let rendered_site: JSX.Element
    if (userName === "") {
        // Before connection
        rendered_site = (
            <div className="flex flex-col m-2 border border-2 border-black items-center">
                <div>Connect to chat</div>
                {userNameInputField}
                <button id="connect" onClick={tryToConnectUser} className="border-2 border-black p-1">
                    Connect
                </button>
                <div>{errorMessage}</div>
            </div>
        )
    } else {
        // After user connected with username
        rendered_site = (
            <div>
                <MyRouter />
                <div className="flex flex-col m-2">
                    <div id="chatbox" className="grid grid-cols-10 overflow-y-auto">
                        {rendered_messages}
                    </div>
                    <div className="grid grid-cols-10 gap-2">
                        <input
                            id="chatinput"
                            className="col-span-9 border-2"
                            type="text"
                            placeholder={"Write something!"}
                            value={chatMessage}
                            onChange={(e) => {
                                setChatMessage(e.target.value)
                            }}
                            onKeyDown={handleKeydown}
                        />
                        <button id="sendmessage" className="col-span-1 border-2" onClick={sendChatMessage}>
                            Send
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return rendered_site
}
