<script lang="ts">
import { Spinner } from "@repo/ui"
import { onMount } from "svelte"
import FileUpload from "$lib/components/FileUpload.svelte"
import ReplayComparison from "$lib/components/ReplayComparison.svelte"
import { type ReplayData, TIMELINE_OPTIONS, type TimelineOption } from "$lib/types"

// For dev mode, we'll load sample data
const is_dev = true

const ip = "http://localhost:8000"
const replay_parse_endpoint = "parse_replay"

let real_replay_data: ReplayData | null = $state(null)
let ideal_replay_data: ReplayData | null = $state(null)
let real_replay_selected_player_id = $state(1)
let ideal_replay_selected_player_id = $state(1)
let timelineSelected: TimelineOption = $state(TIMELINE_OPTIONS[0])
let swapped = $state(false)
let loading = $state(false)

async function parseReplay(replay_file: File): Promise<ReplayData> {
    const second = 22.4
    const formData = new FormData()
    formData.append("replay_tick", `${second * 10}`)
    formData.append("replay_file", replay_file)

    const response = await fetch(`${ip}/${replay_parse_endpoint}`, {
        method: "POST",
        body: formData,
    })
    if (response.ok) {
        return await response.json()
    }
    return {} as ReplayData
}

async function handleFilesSelect(e: Event, playerId: 1 | 2) {
    const input = e.target as HTMLInputElement
    const files = input.files
    if (!files || files.length === 0) {
        return
    }

    loading = true
    try {
        const replay_data = await parseReplay(files[0])
        if (playerId === 1) {
            real_replay_data = replay_data
        } else {
            ideal_replay_data = replay_data
        }
    } catch (error) {
        console.error("Error parsing replay:", error)
    } finally {
        loading = false
    }
}

function handleSwap() {
    swapped = !swapped
}

// Sample data for development
const sampleReplayData: ReplayData = {
    player1: { name: "Player1" },
    player2: { name: "Player2" },
    timeline: [
        [
            {
                gameloop: 0,
                workers_active: 12,
                workers_produced: 12,
                workers_lost: 0,
                supply: 13,
                supply_cap: 15,
                supply_block: 0,
                spm: 0,
                total_army_value: 0,
                total_resources_lost: 0,
                total_resources_collected: 200,
                workers_killed: 0,
                resource_collection_rate_all: 200,
            },
            {
                gameloop: 0,
                workers_active: 12,
                workers_produced: 12,
                workers_lost: 0,
                supply: 13,
                supply_cap: 15,
                supply_block: 0,
                spm: 0,
                total_army_value: 0,
                total_resources_lost: 0,
                total_resources_collected: 200,
                workers_killed: 0,
                resource_collection_rate_all: 200,
            },
        ],
        [
            {
                gameloop: 224,
                workers_active: 14,
                workers_produced: 14,
                workers_lost: 0,
                supply: 15,
                supply_cap: 16,
                supply_block: 0,
                spm: 0.5,
                total_army_value: 0,
                total_resources_lost: 0,
                total_resources_collected: 400,
                workers_killed: 0,
                resource_collection_rate_all: 220,
            },
            {
                gameloop: 224,
                workers_active: 16,
                workers_produced: 16,
                workers_lost: 0,
                supply: 17,
                supply_cap: 18,
                supply_block: 0,
                spm: 0.6,
                total_army_value: 0,
                total_resources_lost: 0,
                total_resources_collected: 450,
                workers_killed: 0,
                resource_collection_rate_all: 250,
            },
        ],
        [
            {
                gameloop: 448,
                workers_active: 18,
                workers_produced: 18,
                workers_lost: 0,
                supply: 18,
                supply_cap: 20,
                supply_block: 0,
                spm: 0.7,
                total_army_value: 100,
                total_resources_lost: 0,
                total_resources_collected: 800,
                workers_killed: 0,
                resource_collection_rate_all: 300,
            },
            {
                gameloop: 448,
                workers_active: 20,
                workers_produced: 20,
                workers_lost: 0,
                supply: 21,
                supply_cap: 22,
                supply_block: 0,
                spm: 0.8,
                total_army_value: 50,
                total_resources_lost: 0,
                total_resources_collected: 900,
                workers_killed: 0,
                resource_collection_rate_all: 350,
            },
        ],
    ],
}

onMount(async () => {
    if (is_dev) {
        real_replay_data = sampleReplayData
        ideal_replay_data = {
            ...sampleReplayData,
            player1: { name: "IdealPlayer1" },
            player2: { name: "IdealPlayer2" },
        }
    }
})
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl mx-auto">
    <h1 class="text-4xl font-bold mb-6 text-center">Replay Comparer</h1>

    <div class="grid grid-cols-3 text-center gap-4 mb-4">
        <FileUpload
            label="Drop your real replay here"
            on_upload={(files) => handleFilesSelect({ target: { files } } as unknown as Event, 1)}
            disabled={loading}
        />
        <div class="flex items-center justify-center">
            <button
                class="btn-primary"
                onclick={handleSwap}
            >
                {swapped ? "=> Swap <=" : "<= Swap =>"}
            </button>
        </div>
        <FileUpload
            label="Drop your ideal replay here"
            on_upload={(files) => handleFilesSelect({ target: { files } } as unknown as Event, 2)}
            disabled={loading}
        />
    </div>

    <div class="grid grid-cols-3 text-center mb-4">
        <div class="font-semibold">Real replay</div>
        <div></div>
        <div class="font-semibold">Ideal replay</div>
    </div>

    {#if loading}
        <div class="flex items-center justify-center p-8">
            <Spinner />
            <span class="ml-3 text-gray-600">Loading...</span>
        </div>
    {:else if real_replay_data !== null && ideal_replay_data !== null}
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
                real_replay_data={ideal_replay_data}
                ideal_replay_data={real_replay_data}
                bind:real_replay_selected_player_id={ideal_replay_selected_player_id}
                bind:ideal_replay_selected_player_id={real_replay_selected_player_id}
                bind:timelineSelected
            />
        {/if}
    {:else}
        <div class="text-center text-gray-500 p-8">Drop two replays above to compare them</div>
    {/if}
</div>
