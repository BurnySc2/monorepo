import React from "react"

type Props = {
    index: number
    id: number
    content: string
    deleteFunction: () => void
}

export default function TodoItem({ index, content, deleteFunction }: Props): JSX.Element {
    return (
        <div className="grid grid-cols-12 mx-2">
            <div className="col-span-2 flex ">
                <div className="mx-2 my-auto">{index + 1})</div>
                <button className="mx-2 p-1  border-2" onClick={deleteFunction}>
                    Delete
                </button>
                {/*<div className="mx-2 my-auto">{id})</div>*/}
            </div>
            <div className="col-span-10 my-auto">{content}</div>
        </div>
    )
}
