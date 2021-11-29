import React from "react"

import MyRouter from "../components/MyRouter"
export default function HomePage(): JSX.Element {
    const name = "world"
    return (
        <div>
            <MyRouter />
            <div className="text-center my-2">
                <div>Hello {name}!</div>
                <div>
                    Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte
                    apps.
                </div>
            </div>
        </div>
    )
}
