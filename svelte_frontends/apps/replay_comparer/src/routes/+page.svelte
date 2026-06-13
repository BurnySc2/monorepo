<script lang="ts">
import { FileUpload, Spinner } from "@repo/ui"
import { onMount } from "svelte"
import { fetch_parse_replay, fetch_replay_events } from "$lib/api"
import ReplayComparison from "$lib/components/ReplayComparison.svelte"
import { type ReplayData, type SavedIdealReplay, TIMELINE_OPTIONS, type TimelineOption } from "$lib/types"

const is_dev = true
const local_storage_key = "saved_ideal_replays"

let real_replay_data: ReplayData | null = $state(null)
let ideal_replay_data: ReplayData | null = $state(null)
let real_replay_selected_player_id = $state(1)
let ideal_replay_selected_player_id = $state(1)
let timeline_selected: TimelineOption = $state(TIMELINE_OPTIONS[0])
let swapped = $state(false)
let loading = $state(false)
let saved_ideals: SavedIdealReplay[] = $state([])
let selected_saved_ideal_name: string = $state("")
let show_saved_ideals_dropdown = $state(false)
let editing_ideal_name: string | null = $state(null)
let new_ideal_name_input: string = $state("")

async function parse_replay(replay_file: File): Promise<ReplayData> {
    const second = 22.4
    return await fetch_parse_replay(replay_file, `${second * 10}`)
}

async function parse_replay_events(replay_file: File): Promise<ReplayData> {
    return await fetch_replay_events(replay_file)
}

function load_saved_ideals(): SavedIdealReplay[] {
    if (typeof window === "undefined") {
        return []
    }
    const stored = localStorage.getItem(local_storage_key)
    if (stored) {
        return JSON.parse(stored) as SavedIdealReplay[]
    }
    return []
}

function save_ideal_replay(name: string, replay_data: ReplayData): void {
    const ideals = load_saved_ideals()
    const existing = ideals.findIndex((i) => i.name === name)
    if (existing >= 0) {
        ideals[existing].replay_data = replay_data
    } else {
        ideals.push({ name, replay_data })
    }
    localStorage.setItem(local_storage_key, JSON.stringify(ideals))
    saved_ideals = load_saved_ideals()
}

function delete_saved_ideal(name: string): void {
    const ideals = load_saved_ideals()
    const filtered = ideals.filter((i) => i.name !== name)
    localStorage.setItem(local_storage_key, JSON.stringify(filtered))
    saved_ideals = filtered
    if (selected_saved_ideal_name === name) {
        selected_saved_ideal_name = ""
    }
}

function rename_saved_ideal(old_name: string, new_name: string): void {
    const ideals = load_saved_ideals()
    const target = ideals.find((i) => i.name === old_name)
    if (target) {
        target.name = new_name
        localStorage.setItem(local_storage_key, JSON.stringify(ideals))
        saved_ideals = load_saved_ideals()
    }
    editing_ideal_name = null
    new_ideal_name_input = ""
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

function handle_swap() {
    swapped = !swapped
}

function handle_save_ideal() {
    if (ideal_replay_data) {
        const name = prompt("Enter name for this ideal replay:")
        if (name?.trim()) {
            save_ideal_replay(name.trim(), ideal_replay_data)
        }
    }
}

function handle_load_saved_ideal(name: string) {
    const ideals = load_saved_ideals()
    const selected = ideals.find((i) => i.name === name)
    if (selected) {
        ideal_replay_data = selected.replay_data
        selected_saved_ideal_name = name
        show_saved_ideals_dropdown = false
    }
}

function start_rename_ideal(name: string) {
    editing_ideal_name = name
    new_ideal_name_input = name
}

function confirm_rename() {
    if (editing_ideal_name && new_ideal_name_input.trim()) {
        rename_saved_ideal(editing_ideal_name, new_ideal_name_input.trim())
    }
}

function cancel_rename() {
    editing_ideal_name = null
    new_ideal_name_input = ""
}

onMount(() => {
    saved_ideals = load_saved_ideals()
})
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl mx-auto">
    <h1 class="text-4xl font-bold mb-6 text-center">Replay Comparer</h1>

    <div class="grid grid-cols-3 text-center gap-4 mb-4">
        <FileUpload
            label="Drop your real replay here"
            on_upload={(files) => handle_files_select({ target: { files } } as unknown as Event, 1)}
            disabled={loading}
        />
        <div class="flex items-center justify-center">
            <button
                class="btn-primary"
                onclick={handle_swap}
            >
                {swapped ? "=> Swap <=" : "<= Swap =>"}
            </button>
        </div>
        <div class="flex flex-col">
            <FileUpload
                label="Drop your ideal replay here"
                on_upload={(files) => handle_files_select({ target: { files } } as unknown as Event, 2)}
                disabled={loading}
            />
            {#if saved_ideals.length > 0}
                <div class="mt-2 relative">
                    <button
                        class="text-sm text-blue-600 hover:text-blue-800 underline"
                        onclick={() => show_saved_ideals_dropdown = !show_saved_ideals_dropdown}
                    >
                        Load saved ideal...
                    </button>
                    {#if show_saved_ideals_dropdown}
                        <div class="absolute z-10 bg-white border rounded shadow-lg mt-1 p-2 min-w-48 text-left">
                            {#each saved_ideals as ideal}
                                <div class="flex items-center justify-between py-1">
                                    {#if editing_ideal_name === ideal.name}
                                        <input
                                            type="text"
                                            bind:value={new_ideal_name_input}
                                            onkeydown={(e) => e.key === "Enter" && confirm_rename()}
                                            class="border px-1 py-0.5 text-sm w-24"
                                        >
                                        <button
                                            class="text-green-600 text-xs px-1"
                                            onclick={confirm_rename}
                                        >
                                            OK
                                        </button>
                                        <button
                                            class="text-gray-500 text-xs px-1"
                                            onclick={cancel_rename}
                                        >
                                            X
                                        </button>
                                    {:else}
                                        <button
                                            class="text-sm text-blue-600 hover:text-blue-800 flex-grow text-left"
                                            onclick={() => handle_load_saved_ideal(ideal.name)}
                                        >
                                            {ideal.name}
                                        </button>
                                        <button
                                            class="text-xs text-gray-500 hover:text-gray-700 px-1"
                                            onclick={() => start_rename_ideal(ideal.name)}
                                        >
                                            rename
                                        </button>
                                        <button
                                            class="text-xs text-red-500 hover:text-red-700 px-1"
                                            onclick={() => delete_saved_ideal(ideal.name)}
                                        >
                                            X
                                        </button>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            {/if}
        </div>
    </div>

    <div class="grid grid-cols-3 text-center mb-4">
        <div class="font-semibold">Real replay</div>
        <div class="flex justify-center">
            {#if ideal_replay_data}
                <button
                    class="text-sm bg-yellow-100 hover:bg-yellow-200 px-2 py-1 rounded border border-yellow-400"
                    onclick={handle_save_ideal}
                >
                    Save as Ideal
                </button>
            {/if}
        </div>
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
                bind:timeline_selected
            />
        {:else}
            <ReplayComparison
                real_replay_data={ideal_replay_data}
                ideal_replay_data={real_replay_data}
                bind:real_replay_selected_player_id={ideal_replay_selected_player_id}
                bind:ideal_replay_selected_player_id={real_replay_selected_player_id}
                bind:timeline_selected
            />
        {/if}
    {:else}
        <div class="text-center text-gray-500 p-8">Drop two replays above to compare them</div>
    {/if}
</div>
