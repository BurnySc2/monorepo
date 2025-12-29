# pyright: reportUnknownMemberType=false

"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx

from routes.replay_pack_builder.index import index as replay_pack_builder


class State(rx.State):
    count: int = 0

    def increment(self) -> None:
        self.count += 1

    def decrement(self) -> None:
        self.count -= 1


def index() -> rx.Component:
    return rx.hstack(
        rx.button(
            "Decrement",
            color_scheme="ruby",
            on_click=State.decrement,  # pyright: ignore[reportArgumentType]
        ),
        rx.heading(State.count, font_size="2em"),
        rx.button(
            "Increment",
            color_scheme="grass",
            on_click=State.increment,  # pyright: ignore[reportArgumentType]
        ),
        rx.button("Log", color_scheme="indigo", on_click=rx.console_log("Hello World!")),
        spacing="4",
        width="100%",
        justify="center",
        height="100vh",
        align="center",
    )


app = rx.App()
app.add_page(index)
app.add_page(replay_pack_builder, route="replay_pack_builder")
