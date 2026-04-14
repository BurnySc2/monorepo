import type { ParsedReplayFile } from "$lib/replay_types"

const API_BASE = "/api"

export async function parse_replay_file(file: File): Promise<ParsedReplayFile> {
    const form_data = new FormData()
    form_data.append("file", file)

    const response = await fetch(`${API_BASE}/parse_replay`, {
        method: "POST",
        body: form_data,
    })

    if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || "Failed to parse replay")
    }

    return response.json()
}
