<script lang="ts">
import { Spinner } from "@repo/ui"
import { onMount } from "svelte"

// Backend URL from environment or default
const backend_url = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000"

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

<div class="login_container">
    {#if is_loading}
        <Spinner />
    {:else if error_message}
        <div class="error">
            <p>{error_message}</p>
            <button onclick={() => { error_message = null; check_login_status(); }}>Retry</button>
        </div>
    {:else if is_logged_in && logged_in_user}
        <div class="logged_in">
            <p>You are logged in via <strong>{logged_in_user.service}</strong> as '{logged_in_user.name}'</p>
            <button
                class="logout_button"
                onclick={handle_logout}
            >
                Log out
            </button>
        </div>
    {:else}
        <div class="login_buttons">
            <button
                class="oauth_button twitch"
                onclick={start_twitch_login}
            >
                Login with Twitch
            </button>
            <button
                class="oauth_button github"
                onclick={start_github_login}
            >
                Login with GitHub
            </button>
            <button
                class="oauth_button google"
                onclick={() => { alert('Google login not implemented yet'); }}
            >
                Login with Google
            </button>
        </div>
    {/if}
</div>

<style>
.login_container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
}

.loading,
.error,
.logged_in {
    text-align: center;
}

.error button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
}

.login_buttons {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
}

.oauth_button {
    padding: 1rem 2rem;
    font-size: 1rem;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    min-width: 200px;
    transition: opacity 0.2s;
}

.oauth_button:hover {
    opacity: 0.9;
}

.oauth_button.twitch {
    background-color: #6441a5;
    color: white;
}

.oauth_button.github {
    background-color: #171515;
    color: white;
}

.oauth_button.google {
    background-color: #4285f4;
    color: white;
}

.logout_button {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
    margin-top: 1rem;
}

.logout_button:hover {
    opacity: 0.9;
}
</style>
