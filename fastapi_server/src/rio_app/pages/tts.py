from functools import partial
from typing import Literal

import rio

from rio_app.components.tts.generate_tts import Voices, generate_tts
from rio_app.components.tts.tts_settings import TTSSettings

VOICES_LIST: list[str] = sorted(v.name for v in Voices)


@rio.page(
    name="TTS",
    url_segment="tts",
)
class LoginRootPage(rio.Component):
    _is_loading: bool = True

    audio_is_generating: bool = False
    audio_b64_data: str = ""

    user_selected_voice: str = ""
    user_written_text: str = ""

    twitch_url_volume: float = 15
    twitch_url_channel_name: str = "burnysc2"

    @rio.event.on_mount
    async def on_mount(self):
        # Load voice from localstorage
        tts_settings = self.session[TTSSettings]
        self.user_selected_voice = tts_settings.voice

        # Selected voice isn't valid, load a default one
        if self.user_selected_voice not in VOICES_LIST:
            self.user_selected_voice = VOICES_LIST[0]
            tts_settings.voice = VOICES_LIST[0]
            self.session.attach(tts_settings)

    async def handle_select_voice(self, event: rio.DropdownChangeEvent[str]):
        tts_settings = self.session[TTSSettings]
        self.user_selected_voice = event.value
        tts_settings.voice = event.value
        self.session.attach(tts_settings)

    async def generate_audio(self):
        self.audio_is_generating = True
        self.audio_b64_data, _ = await generate_tts(Voices[self.user_selected_voice], self.user_written_text)
        self.audio_is_generating = False

    @property
    def preview_text(self) -> str:
        return f"{self.user_selected_voice.lower()}: {self.user_written_text}"

    @property
    def browser_source_url(self) -> str:
        return f"https://burnysc2.xyz/tts/twitch/{self.twitch_url_channel_name}?volume={self.twitch_url_volume:d}"

    async def copy_to_clipboard(self, trigger: Literal["chat_text", "overlay_link"]):
        if trigger == "chat_text":
            await self.session.set_clipboard(self.preview_text)
        elif trigger == "overlay_link":
            await self.session.set_clipboard(self.browser_source_url)

    def build(self) -> rio.Component:
        audio_element = rio.Text(
            "Audio will appear here",
            # pyrefly: ignore
            align_x=0.5,
        )
        if self.audio_is_generating:
            audio_element = rio.ProgressCircle(align_x=0.5, align_y=0.5)
        elif self.audio_b64_data != "":
            audio_element = rio.Webview(
                f"""
<audio controls>
    <source src="data:audio/mpeg;base64, {self.audio_b64_data}" type="audio/mpeg" />
    Your browser does not support the audio element.
</audio>
""".strip()
            )

        return rio.Column(
            rio.Text("Text-to-speech Generator", style="heading1"),
            # List voices
            rio.Dropdown(VOICES_LIST, label="Voice", on_change=self.handle_select_voice),
            # Input text
            rio.TextInput(
                text=self.bind().user_written_text,
                label="Text to convert to TTS",
            ),
            rio.Row(
                # Preview (copyable text to chat)
                rio.TextInput(
                    text=self.preview_text,
                    label="Copyable text to twitch chat",
                    # pyrefly: ignore
                    grow_x=True,
                ),
                # Button to copy to clipboard
                rio.Button(
                    "Copy",
                    on_press=partial(self.copy_to_clipboard, "chat_text"),
                    # pyrefly: ignore
                    align_x=1,
                ),
            ),
            # Generate audio button, disable when text is empty
            rio.Button("Generate audio", is_sensitive=self.user_written_text != "", on_press=self.generate_audio),
            # Audio preview (with playback)
            audio_element,
            rio.Spacer(min_height=5),
            # Instruction for overlay setup
            rio.Text("OBS Overlay Setup", style="heading2"),
            rio.Text(
                "You can add this TTS as an overlay in OBS by adding this URL as a browser source (replace the channel name with your Twitch username):",  # noqa: E501
                overflow="wrap",
            ),
            # Input field for channel name
            rio.TextInput(text=self.bind().twitch_url_channel_name, label="Twitch channel name"),
            rio.NumberInput(
                value=self.bind().twitch_url_volume, label="Audio volume (0-100)", decimals=0, minimum=0, maximum=100
            ),
            rio.Row(
                # Copyable-URL field
                rio.TextInput(
                    text=self.browser_source_url,
                    label="Browser source url",
                    # pyrefly: ignore
                    grow_x=True,
                ),
                #  Button to copy to clipboard
                rio.Button(
                    "Copy",
                    on_press=partial(self.copy_to_clipboard, "overlay_link"),
                    # pyrefly: ignore
                    align_x=1,
                ),
            ),
            min_width=30,
            spacing=0.5,
            align_x=0.5,
            align_y=0.5,
        )
