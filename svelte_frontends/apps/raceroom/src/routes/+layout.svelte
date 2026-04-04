<script lang="ts">
import "../app.css"
import { Navigation } from "@repo/ui"

let { children } = $props()
</script>

<svelte:head></svelte:head>

<Navigation currentApp="Raceroom" />

{@render children?.()}
