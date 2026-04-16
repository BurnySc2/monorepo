import { z } from "zod"
import { browser } from "$app/environment"

export const TtsSettingsSchema = z.object({
    selected_voice_index: z.number().int().min(0).default(0),
})

export type TtsSettings = z.infer<typeof TtsSettingsSchema>

const STORAGE_KEY = "tts_settings"

export function load_tts_settings(): TtsSettings {
    if (!browser) {
        return { selected_voice_index: 0 }
    }
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
            return TtsSettingsSchema.parse(JSON.parse(stored))
        }
    } catch {
        return { selected_voice_index: 0 }
    }
    return { selected_voice_index: 0 }
}

export function save_tts_settings(settings: TtsSettings): void {
    if (!browser) {
        return
    }
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
    } catch {}
}
