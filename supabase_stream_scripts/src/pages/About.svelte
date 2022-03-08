<script lang="ts">
    import { onMount } from "svelte"

    export let defaultText = "this text"
    let someText = defaultText

    onMount(async () => {
        let response = await fetch("https://www.nephest.com/sc2/api/characters?name=BuRny")
        console.log(response)
        console.log(await response.json())
    })
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
