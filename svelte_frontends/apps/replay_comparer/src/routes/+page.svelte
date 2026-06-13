<script lang="ts">
import { FileUpload, Spinner } from "@repo/ui"
import { fetch_parse_replay, fetch_replay_events } from "$lib/api"
import ReplayComparison from "$lib/components/ReplayComparison.svelte"
import { type ReplayData, TIMELINE_OPTIONS, type TimelineOption } from "$lib/types"

let real_replay_data: ReplayData | null = $state(null)
let ideal_replay_data: ReplayData | null = $state(null)
let real_replay_selected_player_id = $state(1)
let ideal_replay_selected_player_id = $state(1)
let timeline_selected: TimelineOption = $state(TIMELINE_OPTIONS[0])
let loading = $state(false)

async function parse_replay(replay_file: File): Promise<ReplayData> {
    const second = 22.4
    return await fetch_parse_replay(replay_file, `${second * 10}`)
}

async function parse_replay_events(replay_file: File): Promise<ReplayData> {
    return await fetch_replay_events(replay_file)
}

async function handle_files_select(e: Event, playerId: 1 | 2) {
    const input = e.target as HTMLInputElement
    const files = input.files
    if (!files || files.length === 0) {
        return
    }

    loading = true
    try {
        const replay_data = await parse_replay(files[0])
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
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl mx-auto">
    <h1 class="text-4xl font-bold mb-6 text-center">Replay Comparer</h1>

    <div class="grid grid-cols-2 text-center gap-4 mb-4">
        <FileUpload
            label="Drop your real replay here"
            on_upload={(files) => handle_files_select({ target: { files } } as unknown as Event, 1)}
            disabled={loading}
        />
        <FileUpload
            label="Drop your ideal replay here"
            on_upload={(files) => handle_files_select({ target: { files } } as unknown as Event, 2)}
            disabled={loading}
        />
    </div>

    <div class="grid grid-cols-2 text-center mb-4">
        <div class="font-semibold">Real replay</div>
        <div class="font-semibold">Ideal replay</div>
    </div>

    {#if loading}
        <div class="flex items-center justify-center p-8">
            <Spinner />
            <span class="ml-3 text-gray-600">Loading...</span>
        </div>
    {:else if real_replay_data !== null && ideal_replay_data !== null}
        <ReplayComparison
            {real_replay_data}
            {ideal_replay_data}
            bind:real_replay_selected_player_id
            bind:ideal_replay_selected_player_id
            bind:timeline_selected
        />
    {:else}
        <div class="text-center text-gray-500 p-8">Drop two replays above to compare them</div>
    {/if}
</div>
