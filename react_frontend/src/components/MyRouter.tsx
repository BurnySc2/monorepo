import React from "react"
import { HashRouter, Routes, Route, Link } from "react-router-dom"
import About from "../pages/About"
import NormalChat from "../pages/NormalChat"
import TodoPage from "../pages/TodoPage"
import HomePage from "../pages/Home"

export default function MyRouter(): JSX.Element {
    return (
        <HashRouter>
            <div>
                {/*Links in header*/}
                <div className="flex justify-center my-2">
                    <Link id="home" className="mx-2 p-1 border-2" to="/">
                        Home
                    </Link>
                    <Link id="about" className="mx-2 p-1 border-2" to="/about">
                        About
                    </Link>
                    <Link id="chat" className="mx-2 p-1 border-2" to="/chat">
                        NormalChat
                    </Link>
                    <Link id="todo" className="mx-2 p-1 border-2" to="/todo">
                        Todo
                    </Link>
                </div>

                {/*What to display based on current page path*/}
                <Routes>
                    <Route path="/about" element={<About />} />
                    <Route path="/chat" element={<NormalChat />} />
                    <Route path="/todo" element={<TodoPage />} />
                    <Route path="/" element={<HomePage />} />
                </Routes>
            </div>
        </HashRouter>
    )
}
