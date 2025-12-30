# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportAttributeAccessIssue=false, reportImplicitOverride=false

import rio


class NameTemplateComponent(rio.Component):
    replay_name_pattern: str = ""

    def build(self) -> rio.Component:
        # TODO Add tooltip
        return rio.Column(
            rio.Text("Name template", style="heading1"),
            rio.Grid(
                [rio.Text("Custom pattern"), rio.TextInput(self.bind().replay_name_pattern, grow_x=True)],
                # TODO Parse example replay and match for preview
                [rio.Text("Preview"), rio.Text(self.replay_name_pattern, overflow="wrap", grow_x=True)],
                column_spacing=1,
                row_spacing=1,
                # align_x=0,
            ),
        )
