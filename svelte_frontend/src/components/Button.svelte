<script lang="ts">
    export let buttonText = "Button text"
    export let onClickFunction = async () => {
        console.log("On click was called")
    }
</script>

<button class="border-2 p-1" on:click={onClickFunction}>{buttonText}</button>
