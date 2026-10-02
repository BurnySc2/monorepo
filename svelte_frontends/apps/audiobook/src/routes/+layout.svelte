<script lang="ts">
import "../app.css"
import { Navigation, Toaster } from "@repo/ui"

let { children } = $props()
</script>

<svelte:head> </svelte:head>

<Navigation currentApp="Audiobook" />
<Toaster />

{@render children?.()}
