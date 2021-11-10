<script lang="ts">
    export let defaultText: string = 'this text'
    let someText = defaultText
</script>

<h1 class="text-center my-2">This is my about page! Here I display features of svelte that I have implemented</h1>
<button
    class="p1 rounded"
    on:click={() => {
        someText = someText === defaultText ? 'is changing' : defaultText
    }}
>
    Click me: {someText}
</button>
