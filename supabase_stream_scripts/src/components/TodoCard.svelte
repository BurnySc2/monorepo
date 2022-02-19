<script lang="ts">
    export let index = 0
    export let cardText = "Some default text"
    export let removeTodo: (index: number) => void
</script>

<main>
    <div class="flex">
        <button class="m-1 p-1 border-2" on:click={() => removeTodo(index)}>Remove</button>
        <div class="m-1 p-1">{index + 1})</div>
        <div class="m-1 p-1">{cardText}</div>
    </div>
</main>
