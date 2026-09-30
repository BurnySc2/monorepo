import { api_fetch } from "@repo/api-client"
import type { operations } from "@repo/api-types"

export const fetch_voices = async (): Promise<
    operations["list_voices_tts_generate_voices_get"]["responses"]["200"]["content"]["application/json"]
> => {
    const resp = await api_fetch("/tts-generate/voices")
    return resp.json()
}

export const fetch_generate_tts = async (
    body: operations["generate_tts_tts_generate_generate_post"]["requestBody"]["content"]["application/json"],
): Promise<
    operations["generate_tts_tts_generate_generate_post"]["responses"]["200"]["content"]["application/json"]
> => {
    const resp = await api_fetch("/tts-generate/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    })
    return resp.json()
}
