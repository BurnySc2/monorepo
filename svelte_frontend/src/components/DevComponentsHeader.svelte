<script lang="ts">
    export let setUrl = () => {}
</script>

<div class="my-2 flex justify-center">
    <button class="m-1 p-1 border-2" id="home" on:click={() => setUrl("/")}>Home</button>
    <button class="m-1 p-1 border-2" id="button" on:click={() => setUrl("/component-button")}>Button</button>
    <button class="m-1 p-1 border-2" id="input" on:click={() => setUrl("/component-input")}>Input</button>
    <button class="m-1 p-1 border-2" id="tournygroup" on:click={() => setUrl("/component-group")}>Tourny Group</button>
    <button class="m-1 p-1 border-2" id="tournygroupstage" on:click={() => setUrl("/component-group-stage")}
        >Tourny Group Stage</button
    >
</div>
