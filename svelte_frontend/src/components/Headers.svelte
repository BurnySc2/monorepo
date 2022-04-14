<script lang="ts">
    import { goto } from "$app/navigation"
</script>

<div class="my2 flex justify-center">
    <button class="m-1 p-1 border-2" id="home" on:click={() => goto("/")}>Home</button>
    <button class="m-1 p-1 border-2" id="about" on:click={() => goto("/about")}>About</button>
    <button class="m-1 p-1 border-2" id="chat" on:click={() => goto("/normalchat")}>Chat</button>
    <button class="m-1 p-1 border-2" id="todo" on:click={() => goto("/todo")}>Todo</button>
    <button class="m-1 p-1 border-2" id="slug" on:click={() => goto("/todo/hello-world")}>Slugs</button>
    <button class="m-1 p-1 border-2" id="browserstorage" on:click={() => goto("/browserstorage")}>BrowserStorage</button
    >
</div>
