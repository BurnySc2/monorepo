import React, { ReactElement, useContext } from "react"
import { ContextProvider } from "./ContextProvider"

export default function ContextConsumer(): ReactElement {
    // @ts-ignore
    const { contextValue, setContextValue } = useContext(ContextProvider)

    console.log(contextValue)

    return (
        <div>
            <div>{contextValue}</div>
            <button
                id="changedata"
                className={"p-1 border-2"}
                onClick={() => {
                    setContextValue(contextValue === "asd" ? "dsa" : "asd")
                }}
            >
                Change data
            </button>
        </div>
    )
}
