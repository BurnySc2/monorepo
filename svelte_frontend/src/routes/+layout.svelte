<script lang="ts">
    console.log(process.env.BACKEND_SERVER)
</script>

<div class="my2 flex justify-center">
    <!-- https://kit.svelte.dev/docs/link-options#data-sveltekit-preload-data -->
    <a class="m-1 p-1 border-2" id="home" data-sveltekit-preload-data="hover" href="/">Home</a>
    <a class="m-1 p-1 border-2" id="about" data-sveltekit-preload-data="hover" href="/about">About</a>
    <a class="m-1 p-1 border-2" id="chat" data-sveltekit-preload-data="hover" href="/normalchat">Chat</a>
    <a class="m-1 p-1 border-2" id="todo" data-sveltekit-preload-data="hover" href="/todo">Todo</a>
    <a class="m-1 p-1 border-2" id="slug" data-sveltekit-preload-data="hover" href="/slug/hello-world">Slugs</a>
    <a class="m-1 p-1 border-2" id="browserstorage" data-sveltekit-preload-data="hover" href="/browserstorage"
        >BrowserStorage</a
    >
</div>
<slot />
