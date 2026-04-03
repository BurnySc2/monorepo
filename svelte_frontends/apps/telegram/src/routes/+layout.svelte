<script lang="ts">
import "../app.css"

let { children } = $props()
</script>

<svelte:head> <title>Telegram Browser</title> </svelte:head>

<div class="flex h-screen flex-col bg-gray-300">
    <!-- Navigation -->
    <nav class="flex items-center gap-4 bg-gray-800 p-4 text-white">
        <a
            href="/"
            class="rounded bg-gray-700 px-4 py-2 hover:bg-gray-600"
            >Home</a
        >
        <span class="text-lg font-bold">Telegram Browser</span>
    </nav>

    {@render children()}
</div>
