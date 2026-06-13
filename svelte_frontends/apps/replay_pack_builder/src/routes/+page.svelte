<script lang="ts">
import { FileUpload, Spinner } from "@repo/ui"
import { onMount } from "svelte"
import { parse_replay_file } from "$lib/api_client"
import FilterPanel from "$lib/components/FilterPanel.svelte"
import FolderUpload from "$lib/components/FolderUpload.svelte"
import ReplayTable from "$lib/components/ReplayTable.svelte"
import {
    DEFAULT_REPLAY_NAME_PATTERN,
    type FilterSettings,
    get_default_filter_settings,
    type ParsedReplayFile,
    rename_file_according_to_template,
    replay_passes_filter,
} from "$lib/replay_types"

let parsed_files: ParsedReplayFile[] = $state([])
let filtered_replays: ParsedReplayFile[] = $state([])
let is_loading = $state(false)
let is_processing = $state(false)
let filter_settings: FilterSettings = $state(get_default_filter_settings())
let replay_name_pattern: string = $state(DEFAULT_REPLAY_NAME_PATTERN)
let preview_name: string = $state("")

// Example replay for preview
const example_replay: ParsedReplayFile = {
    user_id: "some_id",
    size: 0,
    md5: "some_md5",
    status: "processed",
    teams: [
        {
            result: "Win",
            players: [
                {
                    clan_tag: "Heroes",
                    name: "BuRny",
                    pick_race: "Terran",
                    play_race: "Terran",
                    is_human: true,
                    mmr: 420,
                },
            ],
        },
        {
            result: "Loss",
            players: [
                {
                    clan_tag: "",
                    name: "Computer (Easy)",
                    pick_race: "Random",
                    play_race: "Zerg",
                    is_human: false,
                    mmr: 42,
                },
            ],
        },
    ],
    played_timestamp: Date.now(),
    game_length_seconds: 1337,
    map_name: "Alcyone LE",
    region_short: "eu",
    expansion: "LotV",
    game_base_build: 1234,
    game_version: "5.0.14",
    game_type: "idk",
    is_ladder: false,
    is_private: false,
    resume_from_replay: false,
}

function update_preview() {
    preview_name = rename_file_according_to_template(example_replay, replay_name_pattern)
}

function update_filters() {
    filtered_replays = parsed_files.filter((replay) => replay_passes_filter(replay, filter_settings))
}

async function handle_file_upload(files: FileList) {
    is_processing = true
    try {
        for (const file of files) {
            if (file.size > 100 * 1024 * 1024) {
                console.warn(`File ${file.name} exceeds 100MB limit`)
                continue
            }

            try {
                const parsed = await parse_replay_file(file)
                if (parsed_files.some((r) => r.md5 === parsed.md5)) {
                    continue
                }
                parsed.file_data = await file.arrayBuffer()
                parsed.file_name = file.name
                parsed_files = [...parsed_files, parsed]
            } catch (error) {
                console.warn(`Failed to parse ${file.name}:`, error)
            }
        }
        update_filters()
    } finally {
        is_processing = false
    }
}

function remove_replay(md5: string) {
    parsed_files = parsed_files.filter((r) => r.md5 !== md5)
    update_filters()
}

function clear_all_files() {
    parsed_files = []
    filtered_replays = []
}

function reset_pattern() {
    replay_name_pattern = DEFAULT_REPLAY_NAME_PATTERN
    update_preview()
}

async function download_zip() {
    if (filtered_replays.length === 0) {
        return
    }

    is_processing = true
    try {
        // Dynamically import JSZip
        const JSZip = (await import("jszip")).default

        const zip = new JSZip()
        for (const replay of filtered_replays) {
            const new_name = rename_file_according_to_template(replay, replay_name_pattern)
            if (replay.file_data) {
                zip.file(`${new_name}.SC2Replay`, replay.file_data)
            }
        }

        const blob = await zip.generateAsync({ type: "blob" })
        const url = URL.createObjectURL(blob)
        const a = document.createElement("a")
        a.href = url
        a.download = "replay_pack.zip"
        a.click()
        URL.revokeObjectURL(url)
    } catch (error) {
        console.error("Error creating zip:", error)
        alert(`Error creating zip: ${error}`)
    } finally {
        is_processing = false
    }
}

onMount(() => {
    update_preview()
})

$effect(() => {
    replay_name_pattern
    update_preview()
})
</script>

<div class="mx-auto p-8">
    <h1 class="text-4xl font-bold mb-6">Replay Pack Builder</h1>

    <!-- Upload Section -->
    <section class="mb-6 p-4 border border-gray-300 rounded">
        <h2 class="mt-0 mb-4">Upload Replays</h2>
        {#if parsed_files.length > 0}
            <button
                class="btn-danger"
                onclick={clear_all_files}
            >
                Remove uploaded files
            </button>
        {/if}
        <p class="text-sm text-gray-600 mt-2">Total replays uploaded: {parsed_files.length}</p>
        <div class="mt-4">
            {#if is_processing}
                <div class="flex items-center justify-center p-8">
                    <Spinner />
                    <span class="ml-3 text-gray-600">Processing replays...</span>
                </div>
            {:else}
                <div class="flex gap-4 items-center">
                    <FileUpload
                        label="Drag & drop .SC2Replay files here"
                        accept=".SC2Replay"
                        disabled={is_processing}
                        on_upload={handle_file_upload}
                    />
                    <FolderUpload
                        label="Select folder..."
                        disabled={is_processing}
                        on_upload={handle_file_upload}
                    />
                </div>
            {/if}
        </div>
    </section>

    <!-- Filter Section -->
    <section class="mb-6 p-4 border border-gray-300 rounded">
        <h2 class="mt-0 mb-4">Replay Filters</h2>
        <FilterPanel
            bind:filter_settings
            replays={parsed_files}
            on_change={update_filters}
        />
    </section>

    <!-- Name Template Section -->
    <section class="mb-6 p-4 border border-gray-300 rounded">
        <h2 class="mt-0 mb-4">Name template</h2>
        <p class="text-sm text-gray-500 mb-4">
            Available placeholders: date, time, duration, map, region, REGION, version, p1name, p1race, p1r, p1mmr,
            p2name, p2race, p2r, p2mmr
        </p>
        <button
            class="btn-secondary mb-4"
            onclick={reset_pattern}
            disabled={replay_name_pattern === DEFAULT_REPLAY_NAME_PATTERN}
        >
            Reset pattern
        </button>
        <label class="block mb-2">
            Custom pattern
            <input
                type="text"
                class="input w-full mt-1"
                bind:value={replay_name_pattern}
            >
        </label>
        <p class="text-sm text-gray-600 mt-2">Preview: {preview_name}</p>
    </section>

    <!-- Download Section -->
    <section class="mb-6 p-4 border border-gray-300 rounded">
        <h2 class="mt-0 mb-4">Download</h2>
        {#if filtered_replays.length > 0}
            <button
                class="btn-primary"
                onclick={download_zip}
                disabled={is_processing}
            >
                Zip and download {filtered_replays.length} replays
            </button>
        {:else}
            <button
                class="btn-primary"
                disabled
            >
                No replays to download
            </button>
        {/if}
    </section>

    <!-- Replay List -->
    {#if parsed_files.length > 0}
        <section class="mb-6 p-4 border border-gray-300 rounded">
            <h2 class="mt-0 mb-4">Uploaded Replays ({filtered_replays.length} passing filters)</h2>
            <ReplayTable
                replays={parsed_files}
                {replay_name_pattern}
                on_remove={remove_replay}
            />
        </section>
    {/if}
</div>
