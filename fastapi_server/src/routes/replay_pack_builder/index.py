from __future__ import annotations

from litestar import Controller, get
from litestar.response import Template


class MyReplayPackBuilderRoute(Controller):
    path = "/sc2-replay-pack-builder"

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(
            template_name="replay_pack_builder/index.html",
            context={},
        )
