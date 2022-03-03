<script lang="ts">
    export let buttonText = "Button text"
    export let onClickFunction = async () => {}
</script>

<button class="border-2 p-1" on:click={onClickFunction()}>{buttonText}</button>
