import type { components } from "@repo/api-types"

type SearchResultItem = components["schemas"]["SearchResultItem"]
type ViewFileResponse = components["schemas"]["ViewFileResponse"]
type QueueFileResponse = components["schemas"]["QueueFileResponse"]
type DeleteFileResponse = components["schemas"]["DeleteFileResponse"]

const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export const fetch_search = async (query: string): Promise<SearchResultItem[]> => {
    const resp = await fetch(`${get_api_base()}/telegram-browser/search?${query}`)
    return resp.json()
}

export const fetch_queue_file = async (id: string): Promise<QueueFileResponse> => {
    const resp = await fetch(`${get_api_base()}/telegram-browser/queue-file/${id}`)
    return resp.json()
}

export const fetch_delete_file = async (id: string): Promise<DeleteFileResponse> => {
    const resp = await fetch(`${get_api_base()}/telegram-browser/delete-file/${id}`, { method: "DELETE" })
    return resp.json()
}

export const fetch_view_file = async (id: string): Promise<ViewFileResponse> => {
    const resp = await fetch(`${get_api_base()}/telegram-browser/view-file/${id}`)
    return resp.json()
}

export const fetch_save_active_columns = async (columns: string[]): Promise<void> => {
    const resp = await fetch(`${get_api_base()}/telegram-browser/save-active-columns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(columns),
    })
    return resp.json()
}
