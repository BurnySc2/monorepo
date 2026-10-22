<script lang="ts">
import "@repo/ui/styles.css"
import { Navigation } from "@repo/ui"

let { children } = $props()
</script>

<svelte:head> <title>Replay Comparer</title> </svelte:head>

<Navigation currentApp="Replay Comparer" />

{@render children?.()}
