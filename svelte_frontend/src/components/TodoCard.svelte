<script lang="ts">
    export let index = 0
    export let cardText = "Some default text"
    export let removeTodo: (index: number) => void
</script>

<main>
    <div class="flex">
        <button class="m1 p1 rounded" on:click={() => removeTodo(index)}>Remove</button>
        <div class="m1 p1">{index + 1})</div>
        <div class="m1 p1">{cardText}</div>
    </div>
</main>
