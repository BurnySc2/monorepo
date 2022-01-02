<script lang="ts">
    export let defaultText = "this text"
    let someText = defaultText
</script>

<h1 class="text-center my-2">This is my about page! Here I display features of svelte that I have implemented</h1>
<button
    class="p-1 border-2"
    on:click={() => {
        someText = someText === defaultText ? "is changing" : defaultText
    }}
>
    Click me: {someText}
</button>
