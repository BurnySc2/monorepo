<script lang="ts">
    import { dev } from "$app/env"
    import { onMount } from "svelte"

    import About from "../pages/About.svelte"
    import BrowserStorage from "../pages/BrowserStorage.svelte"
    import Home from "../pages/Home.svelte"
    import NormalChat from "../pages/NormalChat.svelte"
    import TodoPage from "../pages/TodoPage.svelte"
    import StreamManager from "../pages/StreamManager.svelte";

    // Router url handling
    let hash: string
    let url: string
    // Header handling for prod vs dev
    let SHOWCOMPONENTS: boolean
    // Required for tests: disallow interaction before GUI is ready
    let mounted = false

    onMount(() => {
        hash = location.hash
        url = hash.slice(1)
        if (url === "") {
            setUrl("/")
        } else {
            SHOWCOMPONENTS = dev && url.startsWith("/component")
        }
        mounted = true
    })

    const setUrl = (newUrl: string) => {
        if (url !== newUrl) {
            url = newUrl
            hash = `#${newUrl}`
            // window.history.replaceState({}, '',`${PATH}/${hash}`)
            window.history.pushState({}, "", `${process.env.BASE_URL || ""}/${hash}`)
            SHOWCOMPONENTS = dev && url.startsWith("/component")
        }
    }
</script>

{#if mounted}
    <div>
        <div class="my2 flex justify-center">
            <button class="m-1 p-1 border-2" id="home" on:click={() => setUrl("/")}>Home</button>
            <button class="m-1 p-1 border-2" id="about" on:click={() => setUrl("/streammanager")}>Stream Manager</button>
            <button class="m-1 p-1 border-2" id="about" on:click={() => setUrl("/about")}>About</button>
            <button class="m-1 p-1 border-2" id="chat" on:click={() => setUrl("/chat")}>Chat</button>
            <button class="m-1 p-1 border-2" id="todo" on:click={() => setUrl("/todo")}>Todo</button>
            <button class="m-1 p-1 border-2" id="browserstorage" on:click={() => setUrl("/browserstorage")}
                >BrowserStorage</button
            >
        </div>

        {#if url === "/"}
            <Home />
        {:else if url === "/streammanager"}
            <StreamManager defaultText="My other text" />
        {:else if url === "/about"}
            <About defaultText="My other text" />
        {:else if url === "/chat"}
            <NormalChat />
        {:else if url === "/todo"}
            <TodoPage />
        {:else if url === "/browserstorage"}
            <BrowserStorage />
        {:else if url === ""}
            <div>Loading...</div>
        {:else}
            <div>You seem to be lost!</div>
        {/if}
    </div>
{/if}
