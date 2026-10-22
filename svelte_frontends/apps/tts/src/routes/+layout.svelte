<script lang="ts">
import "../app.css"
import { Navigation } from "@repo/ui"
import { page } from "$app/state"

let { children } = $props()

const show_nav = !page.url.pathname.startsWith("/overlay")
const page_title = page.url.pathname.startsWith("/overlay") ? "TTS Overlay" : "TTS"
</script>

<svelte:head> <title>{page_title}</title> </svelte:head>

{#if show_nav}
    <Navigation currentApp="TTS" />
{/if}

{@render children?.()}
