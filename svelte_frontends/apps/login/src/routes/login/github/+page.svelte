<script lang="ts">
import { onMount } from "svelte"

let is_loading = true

onMount(() => {
    // The OAuth callback processing happens on the FastAPI backend
    // After processing, the backend redirects to /login
    // This page just shows a loading indicator while that happens
    // Wait a moment then redirect to login
    setTimeout(() => {
        window.location.href = "/login"
    }, 2000)
})
</script>

<div class="callback_container">
    <div class="loading">
        <p>Logging in with GitHub...</p>
    </div>
</div>

<style>
.callback_container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
}

.loading {
    text-align: center;
}
</style>
