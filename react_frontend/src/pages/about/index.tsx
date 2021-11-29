import React from "react"
import MyRouter from "../../components/MyRouter"

export default function About(): JSX.Element {
    return (
        <div>
            <MyRouter />
            <div className="text-center my-2">
                This is my about page! Here I display features of svelte that I have implemented
            </div>
        </div>
    )
}
