<script lang="ts">
    import TodoPage from "../pages/TodoPage.svelte"
    import Home from "../pages/Home.svelte"
    import About from "../pages/About.svelte"
    import GraphqlChat from "../pages/GraphqlChat.svelte"
    import NormalChat from "../pages/NormalChat.svelte"
    import BrowserStorage from "../pages/BrowserStorage.svelte"
    import { onMount } from "svelte"
    import { dev } from "$app/env"
    import Login from "../pages/Login.svelte"
    import DevRouterHeader from "../components/DevComponentsHeader.svelte"
    import DevComponents from "../components/DevComponents.svelte"

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
        {#if SHOWCOMPONENTS}
            <!-- Show different header when showing dev components -->
            <DevRouterHeader {setUrl} />
        {:else}
            <div class="my2 flex justify-center">
                <button class="m-1 p-1 border-2" id="home" on:click={() => setUrl("/")}>Home</button>
                <button class="m-1 p-1 border-2" id="about" on:click={() => setUrl("/about")}>About</button>
                <button class="m-1 p-1 border-2" id="login" on:click={() => setUrl("/login")}>Login</button>
                <button class="m-1 p-1 border-2" id="chat" on:click={() => setUrl("/chat")}>Chat</button>
                <button class="m-1 p-1 border-2" id="graphqlchat" on:click={() => setUrl("/graphqlchat")}
                    >Graphql Chat</button
                >
                <button class="m-1 p-1 border-2" id="todo" on:click={() => setUrl("/todo")}>Todo</button>
                <button class="m-1 p-1 border-2" id="browserstorage" on:click={() => setUrl("/browserstorage")}
                    >BrowserStorage</button
                >
                {#if dev}
                    <!-- Dev Components -->
                    <button class="m-1 p-1 border-2" id="components" on:click={() => setUrl("/components")}
                        >Components</button
                    >
                {/if}
            </div>
        {/if}

        {#if url === "/"}
            <Home />
        {:else if url === "/about"}
            <About defaultText="My other text" />
        {:else if url === "/login"}
            <Login />
        {:else if url === "/chat"}
            <NormalChat />
        {:else if url === "/graphqlchat"}
            <GraphqlChat />
        {:else if url === "/todo"}
            <TodoPage />
        {:else if url === "/browserstorage"}
            <BrowserStorage />
        {:else if url === ""}
            <div>Loading...</div>
        {:else if SHOWCOMPONENTS}
            <!-- Dev Components -->
            <DevComponents bind:url />
        {:else}
            <div>You seem to be lost!</div>
        {/if}
    </div>
{/if}
