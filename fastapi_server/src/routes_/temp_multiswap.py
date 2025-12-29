"""
An example of how to swap multiple elements (1 to 1 ratio) in one request.
"""

from __future__ import annotations

import random
from typing import Annotated

from litestar import Controller, get, post
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template


class MyMultiswapRoute(Controller):
    path = "/multi-swap-test"

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(
            template_name="multiswap/temp_multiswap_index.html",
            context={
                # Initially visible elements
                "items": [
                    {
                        "id": f"element{i}",
                        "text": f"Click me to refresh{i}",
                    }
                    for i in range(1, 10)
                ]
            },
        )

    @post("/update-refresher")
    async def update_refresher(
        self,
        add_refresh: str,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        # Update the "#refresher" element telling it which items are still being processed and polled for

        # In this endpoint, one item "add_refresh" is being added
        # and included to the items already pending in the "input" element
        refresh_items = [add_refresh]
        if data["refresher"] != "":
            refresh_items += data["refresher"].split(";")
        return Template(
            template_name="multiswap/temp_multiswap.html",
            context={
                "refresh_items": refresh_items,
                "items": [
                    {
                        "id": add_refresh,
                        "text": "Loading content soon",
                    },
                ],
            },
        )

    @post("/swap-elements")
    async def swap_elements(
        self,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        # Load data for elements, for example from a database
        elements_to_update = data["refresher"].split(";")
        # In this case random elements between 0 and 2 are picked to simulate being "updated"
        updated_elements = random.sample(elements_to_update, k=random.randint(0, min(2, len(elements_to_update))))
        remaining_elements = [i for i in elements_to_update if i not in updated_elements]
        return Template(
            template_name="multiswap/temp_multiswap.html",
            context={
                # Tell the "#refresher" which items are still pending
                "refresh_items": remaining_elements,
                # Return the context of items for which data became available
                "items": [
                    {
                        "id": element_id,
                        "text": "Element content loaded!",
                    }
                    for element_id in updated_elements
                ],
            },
        )
