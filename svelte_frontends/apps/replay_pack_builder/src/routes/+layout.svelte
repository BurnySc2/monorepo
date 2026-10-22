<script lang="ts">
import "../app.css"
import { Navigation, Toaster } from "@repo/ui"

let { children } = $props()
</script>

<svelte:head> <title>Replay Pack Builder</title> </svelte:head>

<Navigation currentApp="Replay Pack Builder" />
<Toaster />

{@render children?.()}
