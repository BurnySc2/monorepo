import React, { useState } from "react"

export default function FunctionalComponentTemplate(): JSX.Element {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const [variable, setVariable] = useState<string>("")

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const myFunction = () => {
        console.log("Hello world!")
    }

    return <div>Hello World</div>
}
