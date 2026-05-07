import type { operations } from "@repo/api-types"

const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export const fetch_voices = async (): Promise<
    operations["list_voices_tts_generate_voices_get"]["responses"]["200"]["content"]["application/json"]
> => {
    const resp = await fetch(`${get_api_base()}/tts-generate/voices`)
    if (!resp.ok) {
        throw new Error(`Failed to fetch voices: ${resp.statusText}`)
    }
    return resp.json()
}

export const fetch_generate_tts = async (
    body: operations["generate_tts_tts_generate_generate_post"]["requestBody"]["content"]["application/json"],
): Promise<
    operations["generate_tts_tts_generate_generate_post"]["responses"]["200"]["content"]["application/json"]
> => {
    const resp = await fetch(`${get_api_base()}/tts-generate/generate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    })
    if (!resp.ok) {
        throw new Error(`Failed to generate TTS: ${resp.statusText}`)
    }
    return resp.json()
}
