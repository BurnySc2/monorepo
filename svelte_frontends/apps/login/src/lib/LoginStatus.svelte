<script lang="ts">
import { Spinner } from "@repo/ui"
import { onMount } from "svelte"

// Backend URL from environment or default
const backend_url = import.meta.env.VITE_API_TARGET || "http://localhost:8000"

// State variables using snake_case
let is_loading = $state(true)
let is_logged_in = $state(false)
let logged_in_user: { id: number; name: string; service: string } | null = $state(null)
let error_message: string | null = $state(null)

// Check login status on mount
async function check_login_status() {
    try {
        const response = await fetch(`${backend_url}/login`, {
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
}

// Start Twitch OAuth flow
function start_twitch_login() {
    window.location.href = `${backend_url}/login/twitch/start`
}

// Start GitHub OAuth flow
function start_github_login() {
    window.location.href = `${backend_url}/login/github/start`
}

// Logout function
async function handle_logout() {
    try {
        const response = await fetch(`${backend_url}/logout`, {
            credentials: "include",
            redirect: "manual",
        })
        // Follow redirect manually to update UI
        if (response.type === "opaque" || response.status === 0) {
            // Redirect happened, reload to check status
            window.location.reload()
        }
    } catch (error) {
        console.error("Logout failed:", error)
        error_message = "Logout failed"
    }
}

onMount(() => {
    check_login_status()
})
</script>

<div class="flex flex-col items-center justify-center min-h-screen p-8 w-full">
    {#if is_loading}
        <Spinner />
    {:else if error_message}
        <div class="text-center">
            <p>{error_message}</p>
            <button onclick={() => { error_message = null; check_login_status(); }}>Retry</button>
        </div>
    {:else if is_logged_in && logged_in_user}
        <div class="text-center">
            <p>You are logged in via <strong>{logged_in_user.service}</strong> as '{logged_in_user.name}'</p>
            <button
                class="mt-4 px-6 py-3 text-base bg-red-600 hover:bg-red-700 text-white rounded-md cursor-pointer shadow-md hover:shadow-lg transition-colors duration-200"
                onclick={handle_logout}
            >
                Log out
            </button>
        </div>
    {:else}
        <div class="flex flex-col gap-4 items-center">
            <button
                class="px-8 py-4 text-base font-medium border-none rounded-md cursor-pointer min-w-[200px] bg-[#6441a5] text-white transition-opacity duration-200 hover:opacity-90 hover:scale-105 shadow-md"
                onclick={start_twitch_login}
            >
                Login with Twitch
            </button>
            <button
                class="px-8 py-4 text-base font-medium border-none rounded-md cursor-pointer min-w-[200px] bg-[#171515] text-white transition-opacity duration-200 hover:opacity-90 hover:scale-105 shadow-md"
                onclick={start_github_login}
            >
                Login with GitHub
            </button>
            <button
                class="px-8 py-4 text-base font-medium border-none rounded-md cursor-pointer min-w-[200px] bg-[#4285f4] text-white transition-opacity duration-200 hover:opacity-90 hover:scale-105 shadow-md"
                onclick={() => { alert('Google login not implemented yet'); }}
            >
                Login with Google
            </button>
        </div>
    {/if}
</div>
