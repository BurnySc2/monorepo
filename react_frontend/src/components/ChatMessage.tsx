import React from "react"
import moment from "moment"

export type Message = {
    timestamp: number
    author: string
    message: string
}

type Props = {
    message: Message
    userName: string
}

export function ChatMessage({ message: { timestamp, author, message }, userName }: Props): JSX.Element {
    const displayed_name = author === userName ? "You" : author
    return (
        <React.Fragment>
            <div className="col-span-1">{moment(timestamp * 1000).format("HH:mm:ss")}</div>
            <div className="col-span-1">{displayed_name}</div>
            <div className="col-span-8">{message}</div>
        </React.Fragment>
    )
}
