<script lang="ts">
    import { onMount } from "svelte"
    import Dropzone from "svelte-file-dropzone"

    import ReplayComparison from "../components/ReplayComparison.svelte"
    import { timelineOptions } from "../functions/constants"

    const dev = (process.env.DEV && process.env.DEV === "true") || false

    let real_replay_data = null
    let ideal_replay_data = null
    let real_replay_selected_player_id = 1
    let ideal_replay_selected_player_id = 1
    let timelineSelected = timelineOptions[0]
    let swapped = false
    let loading = false

    const ip = process.env.BACKEND_SERVER || "http://localhost:8000"
    const replay_parse_endpoint = "parse_replay"

    const parseReplay = async (replay_file) => {
        let second = 22.4
        const formData = new FormData()
        formData.append("replay_tick", `${second * 10}`)
        formData.append("replay_file", replay_file)

        let response = await fetch(`${ip}/${replay_parse_endpoint}`, {
            method: "POST",
            body: formData,
        })
        if (response.ok) {
            let data = await response.json()
            console.log(data)
            return data
        }
        return {}
    }

    const handleFilesSelect = async (e, playerId: number) => {
        const { acceptedFiles } = e.detail
        console.log(acceptedFiles)
        loading = true
        let replay_data = await parseReplay(acceptedFiles[0])
        if (playerId == 1) {
            real_replay_data = replay_data
        } else {
            ideal_replay_data = replay_data
        }
        loading = false
    }

    onMount(async () => {
        if (dev) {
            const replays = await import("../functions/fake_replay_data")
            real_replay_data = replays.replay1
            ideal_replay_data = replays.replay2
            console.log(real_replay_data)
            console.log(ideal_replay_data)
        }
    })
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl">
    <div class="grid grid-cols-3 text-center">
        <Dropzone on:drop={(e) => handleFilesSelect(e, 1)}>Drop your real replay here</Dropzone>
        <div />
        <Dropzone on:drop={(e) => handleFilesSelect(e, 2)}>Drop your ideal replay here</Dropzone>
    </div>
    <div class="grid grid-cols-3 text-center">
        <div>Real replay</div>
        <button
            on:click={() => {
                swapped = !swapped
            }}>{"<= Swap =>"}</button
        >
        <div>Ideal replay</div>
    </div>
    {#if real_replay_data !== null && ideal_replay_data !== null && !loading}
        {#if !swapped}
            <ReplayComparison
                {real_replay_data}
                {ideal_replay_data}
                bind:real_replay_selected_player_id
                bind:ideal_replay_selected_player_id
                bind:timelineSelected
            />
        {:else}
            <ReplayComparison
                ideal_replay_data={real_replay_data}
                real_replay_data={ideal_replay_data}
                bind:real_replay_selected_player_id={ideal_replay_selected_player_id}
                bind:ideal_replay_selected_player_id={real_replay_selected_player_id}
                bind:timelineSelected
            />
        {/if}
    {:else if loading}
        Loading...
    {/if}
</div>
