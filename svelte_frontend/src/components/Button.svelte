<script>
    export let buttonText = "Button text"
    export let onClickFunction = async () => {}
</script>

<button on:click={onClickFunction()}>{buttonText}</button>
