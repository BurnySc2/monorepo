import { api_fetch } from "@repo/api-client"

export interface User {
    id: number
    name: string
    service: string
}

export interface LoginState {
    is_loading: boolean
    is_logged_in: boolean
    logged_in_user: User | null
    error_message: string | null
}

export async function fetch_login_status(): Promise<{
    logged_in: boolean
    user?: { id: number; name: string; service: string }
}> {
    const response = await api_fetch("/login")
    return response.json()
}

export async function check_login_status(): Promise<LoginState> {
    let is_loading = true
    let is_logged_in = false
    let logged_in_user: User | null = null
    let error_message: string | null = null

    try {
        const data = await fetch_login_status()
        is_logged_in = data.logged_in
        if (data.logged_in && data.user) {
            logged_in_user = { id: data.user.id, name: data.user.name, service: data.user.service }
        }
    } catch (error) {
        console.error("Failed to check login status:", error)
        error_message = "Failed to connect to server"
    } finally {
        is_loading = false
    }

    return { is_loading, is_logged_in, logged_in_user, error_message }
}
