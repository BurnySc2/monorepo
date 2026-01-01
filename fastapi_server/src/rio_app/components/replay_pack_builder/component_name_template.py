# pyright: reportImplicitOverride=false

import arrow
import rio

from rio_app.components.replay_pack_builder.models import ParsedReplayFile

example_replay = ParsedReplayFile(
    **{  # pyright: ignore[reportArgumentType]
        "user_id": "some_id",
        "size": 0,
        "md5": "some_md5",
        "status": "processed",
        "teams": [
            {
                "result": "Win",
                "players": [
                    {
                        "clan_tag": "Heroes",
                        "name": "BuRny",
                        "pick_race": "Terran",
                        "play_race": "Terran",
                        "is_human": True,
                        "mmr": 420,
                    }
                ],
            },
            {
                "result": "Loss",
                "players": [
                    {
                        "clan_tag": "",
                        "name": "Computer (Easy)",
                        "pick_race": "Random",
                        "play_race": "Zerg",
                        "is_human": False,
                        "mmr": 42,
                    }
                ],
            },
        ],
        "played_timestamp": arrow.utcnow().timestamp(),
        "game_length_seconds": 1337,
        "map_name": "Alcyone LE",
        "region_short": "eu",
        "expansion": "LotV",
        "game_base_build": 1234,
        "game_version": "5.0.14",
        "game_type": "idk",
        "is_ladder": False,
        "is_private": False,
        "resume_from_replay": False,
    }
)


class NameTemplateComponent(rio.Component):
    replay_name_pattern: str = ""

    def build(self) -> rio.Component:
        # TODO Add tooltip
        return rio.Column(
            rio.Row(
                rio.Text("Name template", style="heading1"),
                rio.Tooltip(
                    rio.Icon("material/info"),
                    tip=r"""
Available placeholders:
{date} 2025_01_01
{time} 13_25_31
{duration} 4m20s
{map} Alcyone_LE
{region} eu
{REGION} EU
{version} 5.0.14
{p1name} BuRny
{p1race} Terran
{p1r} T
{p1mmr} 1234 (only available in matchmaking)
{p2name}
{p2race}
{p2r}
{p2mmr} (only available in matchmaking)
""".strip(),
                ),
                align_x=0,
                spacing=0.5,
            ),
            rio.Grid(
                [rio.Text("Custom pattern"), rio.TextInput(self.bind().replay_name_pattern, grow_x=True)],
                # TODO Parse example replay and match for preview
                [
                    rio.Text("Preview"),
                    rio.Text(
                        example_replay.rename_file_according_to_template(self.replay_name_pattern),
                        overflow="wrap",
                        grow_x=True,
                    ),
                ],
                column_spacing=1,
                row_spacing=1,
                # align_x=0,
            ),
        )
