import React from "react"

export default function HomePage(): JSX.Element {
    const name = "world"
    return (
        <div className="text-center my-2">
            <div>Hello {name}!</div>
            <div>
                Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte apps.
            </div>
        </div>
    )
}
