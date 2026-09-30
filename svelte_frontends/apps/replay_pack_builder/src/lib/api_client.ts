import { api_fetch } from "@repo/api-client"
import type { ParsedReplayFile } from "$lib/replay_types"

export async function parse_replay_file(file: File): Promise<ParsedReplayFile> {
    const form_data = new FormData()
    form_data.append("file", file)

    const response = await api_fetch("/api/parse_replay", {
        method: "POST",
        body: form_data,
    })

    return response.json()
}
