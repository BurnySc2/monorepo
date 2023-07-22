<script lang="ts">
    console.log(process.env.BACKEND_SERVER)
</script>

<header>
    <div class="my2 flex justify-center">
        <!-- https://kit.svelte.dev/docs/link-options#data-sveltekit-preload-data -->
        <a id="home" data-sveltekit-preload-data="hover" href="/">Home</a>
        <a id="about" data-sveltekit-preload-data="hover" href="/about">About</a>
        <a id="chat" data-sveltekit-preload-data="hover" href="/normalchat">Chat</a>
        <a id="todo" data-sveltekit-preload-data="hover" href="/todo">Todo</a>
        <a id="slug" data-sveltekit-preload-data="hover" href="/slug/hello-world">Slugs</a>
        <a id="browserstorage" data-sveltekit-preload-data="hover" href="/browserstorage">Browser Storage</a>
        <a id="templates/site" data-sveltekit-preload-data="hover" href="/templates/site">Website Template</a>
    </div>
</header>
<slot />

<style>
    div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
    }
    a {
        margin: 0.5rem;
        padding: 0.5rem;
        border-radius: 0.5rem;
        border: 1px solid black;
    }
</style>
