import React, { Component, ReactElement } from "react"
import MyRouter from "./components/MyRouter"

class App extends Component {
    render(): ReactElement {
        return (
            <div>
                <MyRouter />
            </div>
        )
    }
}

export default App
