<script lang="ts">
    export let descriptionText = "Description text"
    export let bindVariable = "Example text"
    export let inputType = "text"
    export let onChangeFunction = async () => {}
</script>

<label class="flex gap-2">
    {descriptionText}
    {#if inputType === "text"}
        <input type="text" bind:value={bindVariable} on:change={onChangeFunction()} />
    {:else if inputType === "email"}
        <input type="email" bind:value={bindVariable} on:change={onChangeFunction()} />
    {:else if inputType === "password"}
        <input type="password" bind:value={bindVariable} on:change={onChangeFunction()} />
    {/if}
</label>
