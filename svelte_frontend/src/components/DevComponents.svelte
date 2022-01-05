<script lang="ts">
    import ButtonExample from "../components/Button.example.svelte"
    import InputfieldExample from "../components/Inputfield.example.svelte"
    import TournyGroupExample from "../components/TournamentGroup.example.svelte"
    import TournyGroupStageExample from "../components/TournamentGroupStage.example.svelte"

    export let url = ""
</script>

{#if url === "/components"}
    <div>TODO List of components</div>
{:else if url === "/component-button"}
    <ButtonExample />
{:else if url === "/component-input"}
    <InputfieldExample />
{:else if url === "/component-group"}
    <TournyGroupExample />
{:else if url === "/component-group-stage"}
    <TournyGroupStageExample />
{:else}
    <div>Component doesn't exist!</div>
{/if}
