<script lang="ts">
    import { onMount } from "svelte"

    import Home from "../pages/Home.svelte"

    // Router url handling
    let hash: string
    let url: string
    // Required for tests: disallow interaction before GUI is ready
    let mounted = false

    onMount(() => {
        hash = location.hash
        url = hash.slice(1)
        if (url === "") {
            setUrl("/")
        }
        mounted = true
    })

    const setUrl = (newUrl: string) => {
        if (url !== newUrl) {
            url = newUrl
            hash = `#${newUrl}`
            // window.history.replaceState({}, '',`${PATH}/${hash}`)
            window.history.pushState({}, "", `${process.env.BASE_URL || ""}/${hash}`)
        }
    }
</script>

{#if mounted}
    <Home />
{/if}
