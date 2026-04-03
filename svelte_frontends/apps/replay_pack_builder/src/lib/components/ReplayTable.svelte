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

<div class="w-full overflow-x-auto">
    <table class="w-full border-collapse">
        <thead>
            <tr>
                <th
                    class="w-10 text-center bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0"
                >
                    <input
                        type="checkbox"
                        class="checkbox cursor-pointer"
                        checked={all_selected}
                        indeterminate={some_selected}
                        onchange={toggle_all}
                    >
                </th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Date</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Map</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Matchup</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Duration</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Region</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Result</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Actions</th>
            </tr>
        </thead>
        <tbody>
            {#each replays as replay (replay.md5)}
                <tr
                    class="hover:bg-gray-50"
                    class:bg-blue-50={selected_md5s.includes(replay.md5)}
                >
                    <td class="w-10 text-center p-3 border-b border-gray-100">
                        <input
                            type="checkbox"
                            class="checkbox cursor-pointer"
                            checked={selected_md5s.includes(replay.md5)}
                            onchange={() => toggle_replay(replay.md5)}
                        >
                    </td>
                    <td class="p-3 border-b border-gray-100">{format_date(replay.played_timestamp)}</td>
                    <td class="p-3 border-b border-gray-100 max-w-48 truncate">{replay.map_name}</td>
                    <td class="p-3 border-b border-gray-100 font-semibold">{get_matchup(replay)}</td>
                    <td class="p-3 border-b border-gray-100">{format_duration(replay.game_length_seconds)}</td>
                    <td class="p-3 border-b border-gray-100">{replay.region_short.toUpperCase()}</td>
                    <td
                        class="p-3 border-b border-gray-100 font-semibold"
                        class:text-green-600={replay.teams[0]?.result === "Win"}
                        class:text-red-600={replay.teams[0]?.result === "Loss"}
                    >
                        {replay.teams[0]?.result || "-"}
                    </td>
                    <td class="p-3 border-b border-gray-100">
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
        <p class="text-center text-gray-500 py-8">No replays uploaded yet.</p>
    {/if}
</div>
