<script lang="ts">
import { type ParsedReplayFile } from "$lib/replay_types"

interface Props {
    replays: ParsedReplayFile[]
    selected_md5s?: string[]
    on_remove: (md5: string) => void
}

let { replays, selected_md5s = $bindable([]), on_remove }: Props = $props()

let all_selected: boolean = $derived(replays.length > 0 && replays.every((r) => selected_md5s.includes(r.md5)))

let some_selected: boolean = $derived(replays.some((r) => selected_md5s.includes(r.md5)) && !all_selected)

function toggle_all() {
    if (all_selected) {
        selected_md5s = []
    } else {
        selected_md5s = replays.map((r) => r.md5)
    }
}

function toggle_replay(md5: string) {
    if (selected_md5s.includes(md5)) {
        selected_md5s = selected_md5s.filter((m) => m !== md5)
    } else {
        selected_md5s = [...selected_md5s, md5]
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
</script>

<div class="table-container">
    <table>
        <thead>
            <tr>
                <th class="checkbox-col">
                    <input
                        type="checkbox"
                        class="checkbox"
                        checked={all_selected}
                        indeterminate={some_selected}
                        onchange={toggle_all}
                    >
                </th>
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
            {#each replays as replay (replay.md5)}
                <tr class:selected={selected_md5s.includes(replay.md5)}>
                    <td class="checkbox-col">
                        <input
                            type="checkbox"
                            class="checkbox"
                            checked={selected_md5s.includes(replay.md5)}
                            onchange={() => toggle_replay(replay.md5)}
                        >
                    </td>
                    <td>{format_date(replay.played_timestamp)}</td>
                    <td class="map-col">{replay.map_name}</td>
                    <td class="matchup-col">{get_matchup(replay)}</td>
                    <td>{format_duration(replay.game_length_seconds)}</td>
                    <td>{replay.region_short.toUpperCase()}</td>
                    <td
                        class:win={replay.teams[0]?.result === "Win"}
                        class:loss={replay.teams[0]?.result === "Loss"}
                    >
                        {replay.teams[0]?.result || "-"}
                    </td>
                    <td>
                        <button
                            class="btn-danger"
                            onclick={() => on_remove(replay.md5)}
                        >
                            Remove
                        </button>
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>

    {#if replays.length === 0}
        <p class="empty-message">No replays uploaded yet.</p>
    {/if}
</div>

<style>
.table-container {
    width: 100%;
    overflow-x: auto;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #eee;
}

th {
    background: #f5f5f5;
    font-weight: 600;
    position: sticky;
    top: 0;
}

.checkbox-col {
    width: 40px;
    text-align: center;
}

.checkbox-col input[type="checkbox"] {
    cursor: pointer;
}

.map-col {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.matchup-col {
    font-weight: 600;
}

tr:hover {
    background: #fafafa;
}

tr.selected {
    background: #eff6ff;
}

.win {
    color: #16a34a;
    font-weight: 600;
}

.loss {
    color: #dc2626;
    font-weight: 600;
}

.empty-message {
    text-align: center;
    color: #888;
    padding: 2rem;
}
</style>
