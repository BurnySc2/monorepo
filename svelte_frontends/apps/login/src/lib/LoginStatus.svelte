<script lang="ts">
import { Spinner } from "@repo/ui"
import { onMount } from "svelte"
import {
    check_login_status,
    type LoginState,
    handle_logout as shared_handle_logout,
    start_github_login,
    start_google_login,
    start_twitch_login,
} from "./login"

let is_loading: LoginState["is_loading"] = $state(true)
let is_logged_in: LoginState["is_logged_in"] = $state(false)
let logged_in_user: LoginState["logged_in_user"] = $state(null)
let error_message: LoginState["error_message"] = $state(null)

// Refresh login status (delegates to canonical check_login_status, keeps Svelte set-state behavior)
async function refresh_login_status() {
    const state = await check_login_status()
    is_loading = state.is_loading
    is_logged_in = state.is_logged_in
    logged_in_user = state.logged_in_user
    error_message = state.error_message
}

// Logout function (delegates to canonical handle_logout, keeps Svelte set-state behavior)
async function handle_logout() {
    try {
        await shared_handle_logout()
        is_logged_in = false
        logged_in_user = null
    } catch (error) {
        console.error("Logout failed:", error)
        error_message = "Logout failed"
    }
}

onMount(() => {
    refresh_login_status()
})
</script>

<div class="flex flex-col items-center justify-center min-h-screen p-8 w-full">
    {#if is_loading}
        <Spinner />
    {:else if error_message}
        <div class="text-center">
            <p>{error_message}</p>
            <button onclick={() => { error_message = null; refresh_login_status(); }}>Retry</button>
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
                onclick={start_google_login}
            >
                Login with Google
            </button>
        </div>
    {/if}
</div>
