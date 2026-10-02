import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

export const TtsSettingsSchema = z.object({
    selected_voice_index: z.number().int().min(0).default(0),
    audio_volume: z.number().int().min(0).max(100).default(100),
})

export type TtsSettings = z.infer<typeof TtsSettingsSchema>

const STORAGE_KEY = "tts_settings"

const persisted = create_persisted_state(STORAGE_KEY, TtsSettingsSchema, TtsSettingsSchema.parse({}))

export const tts_settings = persisted.state

export const is_loading = persisted.is_loading

export function reset_tts_settings(): void {
    persisted.reset()
}
