<script lang="ts">
import { onMount } from "svelte"
import { goto } from "$app/navigation"

/** Shape of the JSON returned by the FastAPI `/login` endpoint */
interface LoginResponse {
    logged_in: boolean
    user?: { id: string; name: string; service: string }
}

let loading = $state(true)
let login: LoginResponse = $state({ logged_in: false })
let error: string | null = $state(null)

onMount(async () => {
    // Detect OAuth error query parameter (e.g. ?error=oauth_failed)
    const url = new URL(window.location.href)
    if (url.searchParams.has("error")) {
        error = url.searchParams.get("error")
    }

    try {
        const res = await fetch("/login", { credentials: "include" })
        login = await res.json()
    } catch (e) {
        error = "network"
    } finally {
        loading = false
    }

    // If not logged in and no explicit error, forward to a provider start page
    if (!login.logged_in && !error) {
        // Default to GitHub – you can change this to another provider if desired
        goto("/login/github/start")
    }
})
</script>

{#if loading}
    <p class="spinner">Checking login…</p>
{:else if error}
    <p class="error">Login failed ({error}). <a href="/login/github/start">Try again</a></p>
{:else if login.logged_in}
    <p>Welcome, {login.user?.name} (via {login.user?.service})!</p>
{/if}
