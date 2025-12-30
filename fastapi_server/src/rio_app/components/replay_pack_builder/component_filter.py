# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false

import arrow
import rio

from rio_app.components.replay_pack_builder.settings import FilterSettings


class MyFilter(rio.Component):
    kind: type[rio.Checkbox | rio.NumberInput | rio.TextInput | rio.DateInput]
    label: str
    filter_settings_key: str

    def set_value(
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
        filter_settings.filtered_replays_need_updating = True
        self.session.attach(filter_settings)

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
    def build(self) -> rio.Component:
        return rio.Column(
            rio.Text("Replay Filters", style="heading1"),
            rio.Tooltip(
                MyFilter(
                    rio.Checkbox,
                    "Filter enabled",
                    "filter_enabled",
                ),
                tip="If unchecked, no replay will be filtered and all replays will be renamed and zipped",
            ),
            rio.Text("Game types", style="heading2"),
            MyFilter(rio.Checkbox, "Matchmaking", "game_matchmaking"),
            MyFilter(rio.Checkbox, "Custom Game", "game_custom"),
            # TODO Add tooltip
            MyFilter(rio.Checkbox, "Include Games with AI", "game_include_games_with_ai"),
            # TODO Add tooltip
            MyFilter(
                rio.Checkbox,
                "Include Games Resumed from Replay",
                "game_include_games_resumed_from_replay",
            ),
            rio.Text("Expansion", style="heading2"),
            MyFilter(rio.Checkbox, "Wings of Liberty", "expansion_wol"),
            MyFilter(rio.Checkbox, "Heart of the Swarm", "expansion_hots"),
            MyFilter(rio.Checkbox, "Legacy of the Void", "expansion_lotv"),
            rio.Text("Server", style="heading2"),
            MyFilter(rio.Checkbox, "Americas", "server_americas"),
            MyFilter(rio.Checkbox, "Europe", "server_europe"),
            MyFilter(rio.Checkbox, "Asia", "server_asia"),
            rio.Text("Date played", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.DateInput, "", "date_played_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.DateInput, "", "date_played_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Game duration (seconds)", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "game_duration_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "game_duration_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Player count", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "player_count_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "player_count_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Average player MMR", style="heading2"),
            rio.Row(
                rio.Text("Between"),
                MyFilter(rio.NumberInput, "", "average_mmr_min", grow_x=True),
                rio.Text("and"),
                MyFilter(rio.NumberInput, "", "average_mmr_max", grow_x=True),
                spacing=0.5,
            ),
            rio.Text("Matchups", style="heading2"),
            rio.Grid(
                [
                    MyFilter(rio.Checkbox, "PvP", "matchup_pvp"),
                    MyFilter(rio.Checkbox, "PvT", "matchup_pvt"),
                    MyFilter(rio.Checkbox, "PvZ", "matchup_pvz"),
                ],
                [
                    MyFilter(rio.Checkbox, "TvT", "matchup_tvt"),
                    MyFilter(rio.Checkbox, "TvZ", "matchup_tvz"),
                    MyFilter(rio.Checkbox, "ZvZ", "matchup_zvz"),
                ],
            ),
            rio.Text("Player name (partial match, case insensitive)", style="heading2"),
            rio.Grid(
                [
                    rio.Text("Must include names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_include",
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "player_name_must_exclude",
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
                        grow_x=True,
                    ),
                ],
                [
                    rio.Text("Must exclude names"),
                    MyFilter(
                        rio.TextInput,
                        "",
                        "map_name_must_exclude",
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
            ),
            spacing=1,
        )
