<script lang="ts">
    export let descriptionText = "Description text"
    export let bindVariable = "Example text"
    export let inputType = "text"
    export let onChangeFunction = () => {
        console.log("On change called")
    }
</script>

<div class="flex gap-2">
    {descriptionText}
    {#if inputType === "text"}
        <label>
            <input type="text" bind:value={bindVariable} on:change={onChangeFunction} />
        </label>
    {:else if inputType === "email"}
        <label>
            <input type="email" bind:value={bindVariable} on:change={onChangeFunction} />
        </label>
    {:else if inputType === "password"}
        <label>
            <input type="password" bind:value={bindVariable} on:change={onChangeFunction} />
        </label>
    {/if}
</div>
