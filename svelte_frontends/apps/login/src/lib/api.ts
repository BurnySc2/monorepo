import { api_fetch } from "@repo/api-client"

export const fetch_login_status = async (): Promise<{
    logged_in: boolean
    user?: { id: number; name: string; service: string }
}> => {
    const resp = await api_fetch("/login")
    return resp.json()
}
