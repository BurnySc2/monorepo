"""
An example of how to swap multiple elements with one template element (many to 1).
"""

from __future__ import annotations

from litestar import Controller, get, post
from litestar.response import Template


class MySwapMultipleRoute(Controller):
    path = "/swap-multiple-test"

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(template_name="swap_multiple/temp_swap_multiple_index.html", context={})

    @post("/execute-swap")
    async def execute_swap(self) -> Template:
        return Template(template_name="swap_multiple/temp_swap_multiple_element.html", context={})
