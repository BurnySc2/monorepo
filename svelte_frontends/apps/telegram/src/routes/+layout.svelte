<script lang="ts">
import "../app.css"

let { children } = $props()
</script>

<svelte:head> <title>Telegram Browser</title> </svelte:head>

{@render children()}
