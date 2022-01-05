<script lang="ts">
    import Inputfield from "./Inputfield.svelte"
    let variable = "Some text"
    let onChangeFunction = () => {
        console.log(`Input was changed to ${variable}`)
    }
</script>

<Inputfield descriptionText="Login" bind:bindVariable={variable} {onChangeFunction} />
