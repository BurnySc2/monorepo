import React from "react"
import Link from "next/link"

export default function MyRouter(): JSX.Element {
    return (
        <div>
            {/*Links in header*/}
            <div className="flex justify-center my-2">
                <Link href="/">
                    <button id="home">Home</button>
                </Link>
                <Link href="/about">
                    <button id="about">About</button>
                </Link>
                <Link href="/normalchat">
                    <button id="normalchat">NormalChat</button>
                </Link>
                <Link href="/todopage">
                    <button id="todopage">Todo</button>
                </Link>
            </div>
        </div>
    )
}
