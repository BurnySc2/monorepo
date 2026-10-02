import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

export const AudioSettingsSchema = z.object({
    value: z.string().default(""),
})

export type AudioSettings = z.infer<typeof AudioSettingsSchema>

const STORAGE_KEY = "audiobook_settings"

const persisted = create_persisted_state(STORAGE_KEY, AudioSettingsSchema, AudioSettingsSchema.parse({ value: "" }))

export const audio_settings = persisted.state

export const is_loading = persisted.is_loading

export function load_audio_settings(): AudioSettings {
    return { ...persisted.state }
}

export function save_audio_settings(settings: AudioSettings): void {
    Object.assign(persisted.state, AudioSettingsSchema.parse(settings))
}

export function reset_audio_settings(): void {
    persisted.reset()
}
