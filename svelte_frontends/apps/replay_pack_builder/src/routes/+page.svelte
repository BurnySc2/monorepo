<script lang="ts">
import { onMount } from "svelte"
import { parse_replay_file } from "$lib/api_client"
import FileUpload from "$lib/components/FileUpload.svelte"
import FilterPanel from "$lib/components/FilterPanel.svelte"
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
let selected_md5s: string[] = $state([])

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
            // Check for duplicates
            const is_duplicate = parsed_files.some((r) => r.file_name === file.name)
            if (is_duplicate) {
                continue
            }

            // 100MB limit
            if (file.size > 100 * 1024 * 1024) {
                console.warn(`File ${file.name} exceeds 100MB limit`)
                continue
            }

            const parsed = await parse_replay_file(file)
            parsed.file_data = await file.arrayBuffer()
            parsed.file_name = file.name
            parsed_files = [...parsed_files, parsed]
        }
        update_filters()
    } catch (error) {
        console.error("Error parsing replay:", error)
        alert(`Error parsing replay: ${error}`)
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
    selected_md5s = []
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

<div class="container">
    <h1>Replay Pack Builder</h1>

    <!-- Upload Section -->
    <section>
        <h2>Upload Replays</h2>
        {#if parsed_files.length > 0}
            <button onclick={clear_all_files}>Remove uploaded files</button>
        {/if}
        <p>Total replays uploaded: {parsed_files.length}</p>
        <FileUpload
            {is_processing}
            on_upload={handle_file_upload}
        />
    </section>

    <!-- Filter Section -->
    <section>
        <h2>Replay Filters</h2>
        <FilterPanel
            bind:filter_settings
            replays={parsed_files}
            on_change={update_filters}
        />
    </section>

    <!-- Name Template Section -->
    <section>
        <h2>Name template</h2>
        <p class="help-text">
            Available placeholders: date, time, duration, map, region, REGION, version, p1name, p1race, p1r, p1mmr,
            p2name, p2race, p2r, p2mmr
        </p>
        <button
            onclick={reset_pattern}
            disabled={replay_name_pattern === DEFAULT_REPLAY_NAME_PATTERN}
        >
            Reset pattern
        </button>
        <label>
            Custom pattern
            <input
                type="text"
                bind:value={replay_name_pattern}
            >
        </label>
        <p>Preview: {preview_name}</p>
    </section>

    <!-- Download Section -->
    <section>
        <h2>Download</h2>
        {#if filtered_replays.length > 0}
            <button
                onclick={download_zip}
                disabled={is_processing}
            >
                Zip and download {filtered_replays.length} replays
            </button>
        {:else}
            <button disabled>No replays to download</button>
        {/if}
    </section>

    <!-- Replay List -->
    {#if parsed_files.length > 0}
        <section>
            <h2>Uploaded Replays ({filtered_replays.length} passing filters)</h2>
            <ReplayTable
                replays={parsed_files}
                bind:selected_md5s
                on_remove={remove_replay}
            />
        </section>
    {/if}
</div>

<style>
.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
}

section {
    margin-bottom: 2rem;
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

h1 {
    margin-bottom: 1.5rem;
}

h2 {
    margin-top: 0;
}

label {
    display: block;
    margin-bottom: 0.5rem;
}

input[type="text"] {
    width: 100%;
    max-width: 300px;
}

.help-text {
    font-size: 0.85rem;
    color: #666;
}

button {
    padding: 0.5rem 1rem;
    background: #4f46e5;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
}

button:hover:not(:disabled) {
    background: #4338ca;
}

button:disabled {
    background: #ccc;
    cursor: not-allowed;
}
</style>
