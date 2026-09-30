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

export function build_overlay_url(channel: string, volume: number): string {
    const safe_channel = encodeURIComponent(channel.trim())
    const safe_volume = clamp_volume_percent(volume)
    return `https://burnysc2.xyz/tts-api/twitch/${safe_channel}?volume=${safe_volume}`
}

export async function copy_to_clipboard(text: string): Promise<void> {
    await navigator.clipboard.writeText(text)
}

export function calculate_reconnect_delay(attempts: number): number {
    const max_delay = 30000
    return Math.min(1000 * 2 ** attempts, max_delay)
}
