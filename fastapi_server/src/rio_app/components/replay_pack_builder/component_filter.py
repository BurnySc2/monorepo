# pyright: reportImplicitOverride=false

import arrow
import rio

from rio_app.components.replay_pack_builder.settings import FilterSettings


class MyFilter(rio.Component):
    kind: type[rio.Checkbox | rio.NumberInput | rio.TextInput | rio.DateInput]
    label: str
    filter_settings_key: str
    on_update_filters: rio.EventHandler[[]] = None

    async def set_value(
        self,
        event: rio.CheckboxChangeEvent | rio.NumberInputChangeEvent | rio.TextInputChangeEvent | rio.DateChangeEvent,
    ):
        filter_settings = self.session[FilterSettings]
        assert self.filter_settings_key in filter_settings.__dict__, self.filter_settings_key
        if isinstance(event, rio.CheckboxChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.is_on)
        if isinstance(event, rio.NumberInputChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.value)
        if isinstance(event, rio.TextInputChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, event.text)
        if isinstance(event, rio.DateChangeEvent):
            filter_settings.__setattr__(self.filter_settings_key, arrow.get(event.value).timestamp())
        self.session.attach(filter_settings)
        await self.call_event_handler(self.on_update_filters)

    def build(self) -> rio.Component:
        filter_settings = self.session[FilterSettings]
        if self.kind == rio.Checkbox:
            return rio.Row(
                rio.Checkbox(filter_settings.__getattribute__(self.filter_settings_key), on_change=self.set_value),  # pyright: ignore[reportAny]
                rio.Text(self.label),
                spacing=1,
                align_x=0,
            )
        elif self.kind == rio.NumberInput:
            return rio.NumberInput(
                filter_settings.__getattribute__(self.filter_settings_key),  # pyright: ignore[reportAny]
                on_change=self.set_value,
                decimals=0,
            )
        elif self.kind == rio.TextInput:
            return rio.TextInput(filter_settings.__getattribute__(self.filter_settings_key), on_change=self.set_value)  # pyright: ignore[reportAny]
        elif self.kind == rio.DateInput:
            return rio.DateInput(
                arrow.get(filter_settings.__getattribute__(self.filter_settings_key)).date(),  # pyright: ignore[reportAny]
                on_change=self.set_value,
            )
        return rio.Text("TODO")


class FilterComponent(rio.Component):
    on_update_filters: rio.EventHandler[[]] = None

    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Replay Filters", style="heading1"),
            rio.Tooltip(
                MyFilter(
                    rio.Checkbox,
                    "Filter enabled",
                    "filter_enabled",
                    self.on_update_filters,
                ),
                tip="""
If unchecked, no replay will be filtered and all replays will be renamed and zipped.
Can be used to simply rename replays.
""".strip(),
            ),
            rio.Text("Game types", style="heading2"),
            MyFilter(rio.Checkbox, "Matchmaking", "game_matchmaking", self.on_update_filters),
            MyFilter(rio.Checkbox, "Custom Game", "game_custom", self.on_update_filters),
            rio.Row(
                MyFilter(rio.Checkbox, "Include Games with AI", "game_include_games_with_ai", self.on_update_filters),
                rio.Tooltip(
                    rio.Icon("material/info"),
                    tip="If unchecked, filters out replays that have at least one AI player.",
                ),
                align_x=0,
                spacing=0.5,
            ),
            rio.Row(
                MyFilter(
                    rio.Checkbox,
                    "Include Games Resumed from Replay",
                    "game_include_games_resumed_from_replay",
                    self.on_update_filters,
                ),
                rio.Tooltip(
                    rio.Icon("material/info"),
                    tip="If unchecked, filters out replays that were resumed from replay.",
                ),
                align_x=0,
                spacing=0.5,
            ),
            rio.Text("Expansion", style="heading2"),
            MyFilter(rio.Checkbox, "Wings of Liberty", "expansion_wol", self.on_update_filters),
            MyFilter(rio.Checkbox, "Heart of the Swarm", "expansion_hots", self.on_update_filters),
            MyFilter(rio.Checkbox, "Legacy of the Void", "expansion_lotv", self.on_update_filters),
            rio.Text("Server", style="heading2"),
            MyFilter(rio.Checkbox, "Americas", "server_americas", self.on_update_filters),
            MyFilter(rio.Checkbox, "Europe", "server_europe", self.on_update_filters),
            MyFilter(rio.Checkbox, "Asia", "server_asia", self.on_update_filters),
            rio.Text("Date played", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.DateInput, "", "date_played_min", self.on_update_filters, grow_x=True),
                rio.Text("and"),
                MyFilter(rio.DateInput, "", "date_played_max", self.on_update_filters, grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Game duration (seconds)", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "game_duration_min", self.on_update_filters, grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "game_duration_max", self.on_update_filters, grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Player count", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "player_count_min", self.on_update_filters, grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "player_count_max", self.on_update_filters, grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Average player MMR", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "average_mmr_min", self.on_update_filters, grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "average_mmr_max", self.on_update_filters, grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Matchups", style="heading2"),
            rio.Grid(
                [
                    MyFilter(rio.Checkbox, "PvP", "matchup_pvp", self.on_update_filters),
                    MyFilter(rio.Checkbox, "PvT", "matchup_pvt", self.on_update_filters),
                    MyFilter(rio.Checkbox, "PvZ", "matchup_pvz", self.on_update_filters),
                ],
                [
                    MyFilter(rio.Checkbox, "TvT", "matchup_tvt", self.on_update_filters),
                    MyFilter(rio.Checkbox, "TvZ", "matchup_tvz", self.on_update_filters),
                    MyFilter(rio.Checkbox, "ZvZ", "matchup_zvz", self.on_update_filters),
                ],
                row_spacing=1,
            ),
            rio.Text("Player name (partial match, case insensitive)", style="heading2"),
            rio.Grid(
                [
                    rio.Text("Must include names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_include",
                        self.on_update_filters,
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_exclude",
                        self.on_update_filters,
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
            ),
            rio.Text("Map name (partial match, case insensitive)", style="heading2"),
            rio.Grid(
                [
                    rio.Text("Must include names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "map_name_must_include",
                        self.on_update_filters,
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "map_name_must_exclude",
                        self.on_update_filters,
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
            ),
            spacing=1,
        )
