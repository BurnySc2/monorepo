import { api_fetch } from "@repo/api-client"
import type { BestTimeEntry, Track } from "$lib/types"

export async function fetch_tracks(): Promise<Track[]> {
    const response = await api_fetch("/api/raceroom/tracks")
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

    const query = params.size > 0 ? `?${params.toString()}` : ""
    const response = await api_fetch(`/api/raceroom/times${query}`)
    return response.json()
}
