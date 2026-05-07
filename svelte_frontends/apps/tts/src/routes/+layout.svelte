<script lang="ts">
import "../app.css"
import { Navigation } from "@repo/ui"
import { page } from "$app/state"

let { children } = $props()

const show_nav = !page.url.pathname.startsWith("/overlay")
</script>

<svelte:head> </svelte:head>

{#if show_nav}
    <Navigation currentApp="TTS" />
{/if}

{@render children?.()}
