// Voice selection guards (B1 OOB fix):
// Stored selected_voice_index may outlive the voices list (e.g., backend
// voices shrink). Clamp OOB to 0 and never throw on preview text.
import type { VoiceInfo } from "@repo/api-types"

export function clamp_voice_index(index: number, voice_count: number): number {
    if (!Number.isInteger(index) || index < 0 || index >= voice_count) {
        return 0
    }
    return index
}

export function get_preview_text(voices: VoiceInfo[], selected_index: number, user_text: string): string {
    if (voices.length === 0) {
        return ""
    }
    const voice = voices[selected_index]
    if (!voice) {
        return ""
    }
    return `${voice.engine}_${voice.label.toLowerCase().replaceAll(" ", "_")}: ${user_text}`
}

// Volume conventions (documented):
// - Percent (0-100) is used in query params and the +page Twitch volume input; fallback is 15 (reasonable OBS level).
// - Ratio (0-1) is used for the HTMLAudioElement volume in the overlay; fallback is 1.0 (full volume).
export function clamp_volume_percent(volume: number): number {
    if (!Number.isFinite(volume)) {
        return 15
    }
    return Math.min(100, Math.max(0, Math.round(volume)))
}

export function clamp_volume_ratio(volume: number): number {
    if (!Number.isFinite(volume)) {
        return 1.0
    }
    return Math.min(1, Math.max(0, volume))
}

export function is_enabled_param(value: string | null): boolean {
    if (value === null) {
        return true
    }
    return !["0", "false", "no", "off"].includes(value.toLowerCase())
}

export function build_overlay_url(
    channel: string,
    volume: number,
    opts?: {
        origin?: string
        allow_mods?: boolean
        allow_vips?: boolean
        allow_subs?: boolean
        allow_normal?: boolean
    },
): string {
    const params = new URLSearchParams({
        stream_name: channel.trim(),
        volume: String(clamp_volume_percent(volume)),
        allow_mods: (opts?.allow_mods ?? true) ? "1" : "0",
        allow_vips: (opts?.allow_vips ?? true) ? "1" : "0",
        allow_subs: (opts?.allow_subs ?? true) ? "1" : "0",
        allow_normal: (opts?.allow_normal ?? true) ? "1" : "0",
    })
    const base = (opts?.origin ?? "").replace(/\/+$/, "")
    return `${base}/overlay?${params.toString()}`
}

export async function copy_to_clipboard(text: string): Promise<void> {
    await navigator.clipboard.writeText(text)
}

export function calculate_reconnect_delay(attempts: number): number {
    const max_delay = 30000
    const safe_attempts = !Number.isFinite(attempts) || attempts < 0 ? 0 : Math.floor(attempts)
    return Math.min(1000 * 2 ** safe_attempts, max_delay)
}
