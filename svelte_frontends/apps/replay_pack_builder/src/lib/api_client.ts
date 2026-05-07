import type { ParsedReplayFile } from "$lib/replay_types"

const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export async function parse_replay_file(file: File): Promise<ParsedReplayFile> {
    const form_data = new FormData()
    form_data.append("file", file)

    const response = await fetch(`${get_api_base()}/api/parse_replay`, {
        method: "POST",
        body: form_data,
    })

    if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || "Failed to parse replay")
    }

    return response.json()
}
