import { get_api_base } from "./base.js"
import { api_fetch } from "./client.js"

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

export function start_twitch_login() {
    window.location.href = `${get_api_base()}/login/twitch/start`
}

export function start_github_login() {
    window.location.href = `${get_api_base()}/login/github/start`
}

export function start_google_login() {
    window.location.href = `${get_api_base()}/login/google/start`
}

export async function handle_logout(): Promise<void> {
    try {
        // Keep raw fetch with redirect manual (never api_fetch) for logout navigation.
        const response = await fetch(`${get_api_base()}/logout`, {
            credentials: "include",
            redirect: "manual",
        })
        if (response.type === "opaque" || response.type === "opaqueredirect" || response.status === 0) {
            window.location.reload()
            return
        }
        if (!response.ok) {
            throw new Error(`Logout failed: ${response.status}`)
        }
        window.location.reload()
    } catch (error) {
        console.error("Logout failed:", error)
        throw new Error("Logout failed")
    }
}
