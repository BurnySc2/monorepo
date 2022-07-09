<script lang="ts">
    export let message = "Player 1 won!"
    export let restartHandler = () => {}
</script>

<div>
    {message}
</div>
<button on:click={restartHandler}>Rematch?</button>
