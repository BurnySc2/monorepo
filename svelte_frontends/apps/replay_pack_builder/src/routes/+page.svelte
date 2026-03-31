<script lang="ts">
import { onMount } from "svelte"
import { parse_replay_file } from "$lib/api_client"
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

async function handle_file_upload(event: Event) {
    const input = event.target as HTMLInputElement
    const files = input.files
    if (!files) {
        return
    }

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

function format_date(timestamp: number): string {
    return new Date(timestamp).toLocaleDateString()
}

function format_duration(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs.toString().padStart(2, "0")}s`
}

function get_matchup(replay: ParsedReplayFile): string {
    if (replay.teams.length !== 2) {
        return "N/A"
    }
    const players = replay.teams.flatMap((t) => t.players)
    if (players.length !== 2) {
        return "N/A"
    }
    return `${players[0].play_race[0]}v${players[1].play_race[0]}`
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
        <input
            type="file"
            accept=".SC2Replay"
            multiple
            onchange={handle_file_upload}
            disabled={is_processing}
        >
        {#if is_processing}
            <p>Processing...</p>
        {/if}
    </section>

    <!-- Filter Section -->
    <section>
        <h2>Replay Filters</h2>

        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.filter_enabled}
                onchange={update_filters}
            >
            Filter enabled
        </label>

        <h3>Game types</h3>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.game_matchmaking}
                onchange={update_filters}
            >
            Matchmaking
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.game_custom}
                onchange={update_filters}
            >
            Custom Game
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.game_include_games_with_ai}
                onchange={update_filters}
            >
            Include Games with AI
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.game_include_games_resumed_from_replay}
                onchange={update_filters}
            >
            Include Games Resumed from Replay
        </label>

        <h3>Expansion</h3>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_wol}
                onchange={update_filters}
            >
            Wings of Liberty
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_hots}
                onchange={update_filters}
            >
            Heart of the Swarm
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_lotv}
                onchange={update_filters}
            >
            Legacy of the Void
        </label>

        <h3>Server</h3>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.server_americas}
                onchange={update_filters}
            >
            Americas
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.server_europe}
                onchange={update_filters}
            >
            Europe
        </label>
        <label>
            <input
                type="checkbox"
                bind:checked={filter_settings.server_asia}
                onchange={update_filters}
            >
            Asia
        </label>

        <h3>Date played</h3>
        <label>
            Between
            <input
                type="date"
                bind:value={filter_settings.date_played_min}
                onchange={update_filters}
            >
            and
            <input
                type="date"
                bind:value={filter_settings.date_played_max}
                onchange={update_filters}
            >
        </label>

        <h3>Game duration (seconds)</h3>
        <label>
            Between
            <input
                type="number"
                bind:value={filter_settings.game_duration_min}
                onchange={update_filters}
            >
            and
            <input
                type="number"
                bind:value={filter_settings.game_duration_max}
                onchange={update_filters}
            >
        </label>

        <h3>Player count</h3>
        <label>
            Between
            <input
                type="number"
                bind:value={filter_settings.player_count_min}
                onchange={update_filters}
            >
            and
            <input
                type="number"
                bind:value={filter_settings.player_count_max}
                onchange={update_filters}
            >
        </label>

        <h3>Average player MMR</h3>
        <label>
            Between
            <input
                type="number"
                bind:value={filter_settings.average_mmr_min}
                onchange={update_filters}
            >
            and
            <input
                type="number"
                bind:value={filter_settings.average_mmr_max}
                onchange={update_filters}
            >
        </label>

        <h3>Matchups</h3>
        <div class="checkbox-grid">
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvp}
                    onchange={update_filters}
                >
                PvP
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvt}
                    onchange={update_filters}
                >
                PvT
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvz}
                    onchange={update_filters}
                >
                PvZ
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_tvt}
                    onchange={update_filters}
                >
                TvT
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_tvz}
                    onchange={update_filters}
                >
                TvZ
            </label>
            <label>
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_zvz}
                    onchange={update_filters}
                >
                ZvZ
            </label>
        </div>

        <h3>Player name (partial match, case insensitive)</h3>
        <label>
            Must include names
            <input
                type="text"
                bind:value={filter_settings.player_name_must_include}
                onchange={update_filters}
            >
        </label>
        <label>
            Must exclude names
            <input
                type="text"
                bind:value={filter_settings.player_name_must_exclude}
                onchange={update_filters}
            >
        </label>

        <h3>Map name (partial match, case insensitive)</h3>
        <label>
            Must include names
            <input
                type="text"
                bind:value={filter_settings.map_name_must_include}
                onchange={update_filters}
            >
        </label>
        <label>
            Must exclude names
            <input
                type="text"
                bind:value={filter_settings.map_name_must_exclude}
                onchange={update_filters}
            >
        </label>
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
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Map</th>
                        <th>Matchup</th>
                        <th>Duration</th>
                        <th>Region</th>
                        <th>Result</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {#each parsed_files as replay}
                        <tr>
                            <td>{format_date(replay.played_timestamp)}</td>
                            <td>{replay.map_name}</td>
                            <td>{get_matchup(replay)}</td>
                            <td>{format_duration(replay.game_length_seconds)}</td>
                            <td>{replay.region_short.toUpperCase()}</td>
                            <td>{replay.teams[0]?.result || "-"}</td>
                            <td><button onclick={() => remove_replay(replay.md5)}>Remove</button></td>
                        </tr>
                    {/each}
                </tbody>
            </table>
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

h3 {
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
}

input[type="text"],
input[type="number"],
input[type="date"] {
    width: 100%;
    max-width: 300px;
}

.help-text {
    font-size: 0.85rem;
    color: #666;
}

.checkbox-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 0.5rem;
    text-align: left;
    border-bottom: 1px solid #eee;
}

th {
    background: #f5f5f5;
}
</style>
