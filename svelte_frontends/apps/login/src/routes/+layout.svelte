<script lang="ts">
import "../app.css"
import { Navigation } from "@repo/ui"

let { children } = $props()
</script>

<svelte:head> <title>Login</title> </svelte:head>

<Navigation currentApp="Login" />

{@render children?.()}
