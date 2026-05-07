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

export async function check_login_status(): Promise<{
    is_loading: boolean
    is_logged_in: boolean
    logged_in_user: User | null
    error_message: string | null
}> {
    let is_loading = true
    let is_logged_in = false
    let logged_in_user: User | null = null
    let error_message: string | null = null

    try {
        const response = await fetch(`/login`, {
            credentials: "include",
        })
        const data = await response.json()
        is_logged_in = data.logged_in
        if (data.logged_in && data.user) {
            logged_in_user = data.user
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
    window.location.href = `/login/twitch/start`
}

export function start_github_login() {
    window.location.href = `/login/github/start`
}

export async function handle_logout(): Promise<void> {
    try {
        const response = await fetch(`/logout`, {
            credentials: "include",
            redirect: "manual",
        })
        if (response.type === "opaque" || response.status === 0) {
            window.location.reload()
        }
    } catch (error) {
        console.error("Logout failed:", error)
        throw new Error("Logout failed")
    }
}
