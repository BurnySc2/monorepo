<script lang="ts">
    import TodoPage from '../pages/TodoPage.svelte'
    import Home from '../pages/Home.svelte'
    import About from '../pages/About.svelte'
    import NormalChat from '../pages/NormalChat.svelte'
    import BrowserStorage from '../pages/BrowserStorage.svelte'
    import { onMount } from 'svelte'
    import { dev } from '$app/env'

    const PATH = dev ? '' : '/fastapi-svelte-template'
    let url = ''
    let hash = ''

    onMount(() => {
        hash = location.hash
        url = hash.slice(1)
        if (url === '') {
            setUrl(url)
        }
    })

    const setUrl = (newUrl: string) => {
        if (url !== newUrl) {
            url = newUrl
            hash = `#${newUrl}`
            // window.history.replaceState({}, '',`${PATH}/${hash}`)
            window.history.pushState({}, '', `${PATH}/${hash}`)
        }
    }
</script>

<main>
    <div class="my2 flex justify-center">
        <button class="m1 p1 rounded" id="home" on:click={() => setUrl('/')}>Home</button>
        <button class="m1 p1 rounded" id="about" on:click={() => setUrl('/about')}>About</button>
        <button class="m1 p1 rounded" id="chat" on:click={() => setUrl('/chat')}>Chat</button>
        <button class="m1 p1 rounded" id="todo" on:click={() => setUrl('/todo')}>Todo</button>
        <button class="m1 p1 rounded" id="browserstorage" on:click={() => setUrl('/browserstorage')}
            >BrowserStorage</button
        >
    </div>
    {#if url === '/'}
        <Home />
    {:else if url === '/about'}
        <About defaultText="My other text" />
    {:else if url === '/chat'}
        <NormalChat />
    {:else if url === '/todo'}
        <TodoPage />
    {:else if url === '/browserstorage'}
        <BrowserStorage />
    {:else if url === ''}
        <div>Loading...</div>
    {:else}
        <div>You seem to be lost!</div>
    {/if}
</main>
