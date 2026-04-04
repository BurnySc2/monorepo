<script lang="ts">
    import "../app.css"
    import { Navigation } from "@repo/ui"
    let { children } = $props()
</script>

<svelte:head> <title>Telegram Browser</title> </svelte:head>

<Navigation currentApp="Telegram" />

{@render children()}
