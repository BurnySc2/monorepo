<script>
    export let setUrl
</script>

<div class="my2 flex justify-center">
    <button class="m1 p1 rounded" id="button" on:click={() => setUrl("/component-button")}>Button</button>
    <button class="m1 p1 rounded" id="input" on:click={() => setUrl("/component-input")}>Input</button>
</div>
