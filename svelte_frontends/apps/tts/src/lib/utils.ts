export function build_overlay_url(channel: string, volume: number): string {
    return `https://burnysc2.xyz/tts-api/twitch/${channel}?volume=${volume}`
}

export async function copy_to_clipboard(text: string): Promise<void> {
    await navigator.clipboard.writeText(text)
}

export function calculate_reconnect_delay(attempts: number): number {
    const max_delay = 30000
    return Math.min(1000 * 2 ** attempts, max_delay)
}
