import { get_api_base } from "./base"

export class ApiError extends Error {
    status: number
    statusText: string
    path: string
    constructor(path: string, status: number, statusText: string) {
        super(`Request failed ${path}: ${status} ${statusText}`)
        this.name = "ApiError"
        this.path = path
        this.status = status
        this.statusText = statusText
    }
}

export function get_api_error_status(error: unknown): number | undefined {
    if (error instanceof ApiError) {
        return error.status
    }
    if (typeof error === "object" && error !== null && "status" in error) {
        const status = (error as { status: unknown }).status
        if (typeof status === "number" && Number.isFinite(status)) {
            return status
        }
    }
    return undefined
}

export async function api_fetch(path: string, init?: RequestInit): Promise<Response> {
    const response = await fetch(`${get_api_base()}${path}`, {
        ...init,
        credentials: init?.credentials ?? "include",
    })
    if (!response.ok) {
        throw new ApiError(path, response.status, response.statusText)
    }
    return response
}
