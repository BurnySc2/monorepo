<script lang="ts">
    import Button from "./Button.svelte"
</script>

<Button
    buttonText="Custom Text"
    onClickFunction={() => {
        console.log("Custom button was clicked!")
    }}
/>
