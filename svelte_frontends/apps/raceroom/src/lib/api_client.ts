import type { BestTimeEntry, Track } from "$lib/types"

const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

const API_BASE = `${get_api_base()}/api/raceroom`

export async function fetch_tracks(): Promise<Track[]> {
    const response = await fetch(`${API_BASE}/tracks`)
    if (!response.ok) {
        throw new Error(`Failed to fetch tracks: ${response.statusText}`)
    }
    return response.json()
}

export async function fetch_times(track_id?: number, start_date?: string, end_date?: string): Promise<BestTimeEntry[]> {
    const params = new URLSearchParams()
    if (track_id !== undefined) {
        params.set("track_id", track_id.toString())
    }
    if (start_date) {
        params.set("start_date", start_date)
    }
    if (end_date) {
        params.set("end_date", end_date)
    }

    const url = `${API_BASE}/times${params.size > 0 ? `?${params.toString()}` : ""}`
    const response = await fetch(url)
    if (!response.ok) {
        throw new Error(`Failed to fetch times: ${response.statusText}`)
    }
    return response.json()
}
