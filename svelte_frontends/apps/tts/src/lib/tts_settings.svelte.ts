import { z } from "zod"
import { browser } from "$app/environment"

export const TtsSettingsSchema = z.object({
    selected_voice_index: z.number().int().min(0).default(0),
    audio_volume: z.number().int().min(0).max(100).default(100),
})

export type TtsSettings = z.infer<typeof TtsSettingsSchema>

const STORAGE_KEY = "tts_settings"

export const tts_settings = $state<TtsSettings>(TtsSettingsSchema.parse({}))
const loading = $state({ value: true })

$effect.root(() => {
    $effect(() => {
        if (browser) {
            if (loading.value) {
                loading.value = false
                const data = localStorage.getItem(STORAGE_KEY)
                if (data !== null) {
                    Object.assign(tts_settings, TtsSettingsSchema.parse(JSON.parse(data)))
                }
            } else {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(tts_settings))
            }
        }

        $state.snapshot(tts_settings)
    })
})
