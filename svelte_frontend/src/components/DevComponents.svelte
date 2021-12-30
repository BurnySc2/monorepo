<script>
    import ButtonExample from "../components/Button.example.svelte"
    import InputfieldExample from "../components/Inputfield.example.svelte"

    export let url = ""
</script>

{#if url === "/components"}
    <div>TODO List of components</div>
{:else if url === "/component-button"}
    <ButtonExample />
{:else if url === "/component-input"}
    <InputfieldExample />
{:else}
    <div>Component doesn't exist!</div>
{/if}
