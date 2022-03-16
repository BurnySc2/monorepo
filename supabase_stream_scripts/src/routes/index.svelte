<script lang="ts">
    import { dev } from "$app/env"
    import { onMount } from "svelte"

    import Home from "../pages/Home.svelte"
    import MatchInfo from "../pages/MatchInfo.svelte"
    import StreamManager from "../pages/StreamManager.svelte"

    // Router url handling
    let hash: string
    let url: string
    // Header handling for prod vs dev
    let SHOWCOMPONENTS: boolean
    // Required for tests: disallow interaction before GUI is ready
    let mounted = false

    let _dontShowHeadersOnUrl = ["/matchinfo"]
    let showHeaders = true

    onMount(() => {
        hash = location.hash
        url = hash.slice(1)
        if (url === "") {
            setUrl("/")
        }
        SHOWCOMPONENTS = dev && url.startsWith("/component")
        _dontShowHeadersOnUrl.forEach((value) => {
            if (url && url.startsWith(value)) {
                showHeaders = false
            }
        })
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
    <div>
        {#if showHeaders}
            <div class="my2 flex justify-center">
                <button class="m-1 p-1 border-2" id="home" on:click={() => setUrl("/")}>Home</button>
                <button class="m-1 p-1 border-2" id="streammanager" on:click={() => setUrl("/streammanager")}
                    >Stream Manager</button
                >
            </div>
        {/if}

        {#if url === "/"}
            <Home />
        {:else if url.startsWith("/streammanager")}
            <StreamManager defaultText="My other text" />
        {:else if url.startsWith("/matchinfo")}
            <MatchInfo />
        {:else if url === ""}
            <div>Loading...</div>
        {:else}
            <div>You seem to be lost!</div>
        {/if}
    </div>
{/if}
