import { api_fetch } from "@repo/api-client"
import type { components } from "@repo/api-types"

type SearchRequest = components["schemas"]["SearchRequest"]
type SearchResultItem = components["schemas"]["SearchResultItem"]
type ViewFileResponse = components["schemas"]["ViewFileResponse"]
type QueueFileResponse = components["schemas"]["QueueFileResponse"]
type DeleteFileResponse = components["schemas"]["DeleteFileResponse"]
type DownloadedFileItem = components["schemas"]["DownloadedFileItem"]
type ChannelNameItem = components["schemas"]["ChannelNameItem"]
type ChannelStatsItem = components["schemas"]["ChannelStatsItem"]

export const fetch_search = async (request: SearchRequest): Promise<SearchResultItem[]> => {
    const resp = await api_fetch("/telegram-browser/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
    })
    return resp.json()
}

export const fetch_queue_file = async (id: string): Promise<QueueFileResponse> => {
    const resp = await api_fetch(`/telegram-browser/queue-file/${id}`)
    return resp.json()
}

export const fetch_delete_file = async (id: string): Promise<DeleteFileResponse> => {
    const resp = await api_fetch(`/telegram-browser/delete-file/${id}`, {
        method: "DELETE",
    })
    return resp.json()
}

export const fetch_view_file = async (id: string): Promise<ViewFileResponse> => {
    const resp = await api_fetch(`/telegram-browser/view-file/${id}`)
    return resp.json()
}

export const fetch_save_active_columns = async (columns: string[]): Promise<void> => {
    await api_fetch("/telegram-browser/save-active-columns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(columns),
    })
}

export const fetch_downloads = async (): Promise<DownloadedFileItem[]> => {
    const resp = await api_fetch("/telegram-browser/downloads")
    return resp.json()
}

export const fetch_channel_names = async (): Promise<ChannelNameItem[]> => {
    const resp = await api_fetch("/telegram-browser/channel-names")
    return resp.json()
}

export const fetch_channel_stats = async (): Promise<ChannelStatsItem[]> => {
    const resp = await api_fetch("/telegram-browser/channel-stats")
    return resp.json()
}
