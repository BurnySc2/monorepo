import { get_api_base } from "./base"

export async function api_fetch(path: string, init?: RequestInit): Promise<Response> {
    const response = await fetch(`${get_api_base()}${path}`, {
        ...init,
        credentials: init?.credentials ?? "include",
    })
    if (!response.ok) {
        throw new Error(`Request failed ${path}: ${response.status} ${response.statusText}`)
    }
    return response
}
