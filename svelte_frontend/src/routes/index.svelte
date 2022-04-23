<script lang="ts">
    import Headers from "../components/Headers.svelte"
    import Home from "../pages/Home.svelte"

    console.log(process.env.BACKEND_SERVER)
</script>

<div>
    <Headers />

    <Home />
</div>
