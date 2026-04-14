import { z } from "zod"
import { browser } from "$app/environment"

export const AudioSettingsSchema = z.object({
    value: z.string().default(""),
})

export type AudioSettings = z.infer<typeof AudioSettingsSchema>

const STORAGE_KEY = "audiobook_settings"

export function load_audio_settings(): AudioSettings {
    if (!browser) {
        return { value: "" }
    }
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
            return AudioSettingsSchema.parse(JSON.parse(stored))
        }
    } catch {
        return { value: "" }
    }
    return { value: "" }
}

export function save_audio_settings(settings: AudioSettings): void {
    if (!browser) {
        return
    }
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {}
}
