import { api_fetch, get_api_error_status } from "@repo/api-client"
import type { ParsedReplayFile } from "$lib/replay_types"

export async function parse_replay_file(file: File): Promise<ParsedReplayFile> {
    const form_data = new FormData()
    form_data.append("file", file)

    try {
        const response = await api_fetch("/api/parse_replay", {
            method: "POST",
            body: form_data,
        })

        return response.json()
    } catch (error) {
        if (get_api_error_status(error) === 409) {
            const friendly = new Error("Replay already uploaded: this replay has already been uploaded")
            ;(friendly as Error & { status?: number }).status = 409
            throw friendly
        }
        throw error
    }
}
