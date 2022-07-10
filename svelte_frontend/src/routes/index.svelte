<script lang="ts">
    import { onMount } from "svelte"

    import Headers from "../components/Headers.svelte"
    import Home from "../pages/Home.svelte"

    console.log(process.env.BACKEND_SERVER)

    let siteLoaded = false
    onMount(() => {
        siteLoaded = true
    })
</script>

{#if siteLoaded}
    <Headers />
    <Home />
{/if}
