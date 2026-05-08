import type { operations } from "@repo/api-types"

export const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export const fetch_login_status = async (): Promise<{ logged_in: boolean; user?: string }> => {
    const resp = await fetch(`${get_api_base()}/login`, { credentials: "include" })
    if (!resp.ok) {
        throw new Error(`Failed to fetch login status: ${resp.statusText}`)
    }
    return resp.json()
}

export const fetch_logout = async (): Promise<
    operations["logout_logout_get"]["responses"]["200"]["content"]["application/json"]
> => {
    const resp = await fetch(`${get_api_base()}/logout`, { method: "POST" })
    if (!resp.ok) {
        throw new Error(`Failed to logout: ${resp.statusText}`)
    }
    return resp.json()
}
