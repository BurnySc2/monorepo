<script lang="ts">
import { type ParsedReplayFile, rename_file_according_to_template } from "$lib/replay_types"

interface Props {
    replays: ParsedReplayFile[]
    replay_name_pattern: string
    on_remove: (md5: string) => void
}

let { replays, replay_name_pattern, on_remove }: Props = $props()

let sorted_replays = $derived([...replays].sort((a, b) => b.played_timestamp - a.played_timestamp))

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
    const team1_players = replay.teams[0].players.length
    const team2_players = replay.teams[1].players.length

    // Team games: 2v2, 3v3, 4v4
    if (team1_players === team2_players && [2, 3, 4].includes(team1_players)) {
        return `${team1_players}v${team2_players}`
    }

    // 1v1
    if (team1_players !== 1 || team2_players !== 1) {
        return "N/A"
    }

    const players = replay.teams.flatMap((t) => t.players)
    const winner = replay.teams[0].result === "Win" ? players[0] : players[1]
    const loser = replay.teams[0].result === "Win" ? players[1] : players[0]
    return `${winner.play_race[0]}v${loser.play_race[0]}`
}

function get_players(replay: ParsedReplayFile): string {
    if (replay.teams.length !== 2) {
        return "N/A"
    }
    const players = replay.teams.flatMap((t) => t.players)
    if (players.length !== 2) {
        return "N/A"
    }
    const winner = replay.teams[0].result === "Win" ? players[0].name : players[1].name
    const loser = replay.teams[0].result === "Win" ? players[1].name : players[0].name
    return `${winner} vs ${loser}`
}

function get_winner_display(replay: ParsedReplayFile): string {
    const winning_team = replay.teams.find((t) => t.result === "Win")
    if (!winning_team) {
        return "-"
    }

    // Check if 1v1: exactly 2 teams, each with exactly 1 player
    const is_1v1 = replay.teams.length === 2 && replay.teams.every((t) => t.players.length === 1)

    if (is_1v1) {
        const winner = winning_team.players[0]
        const race_letter = winner.play_race[0] ?? ""
        return `[${race_letter}] ${winner.name}`
    }

    // Not 1v1: show "Team N"
    const team_index = replay.teams.indexOf(winning_team)
    return `Team ${team_index + 1}`
}

async function download_replay(replay: ParsedReplayFile) {
    if (!replay.file_data) {
        return
    }
    const new_name = rename_file_according_to_template(replay, replay_name_pattern)
    const blob = new Blob([replay.file_data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${new_name}.SC2Replay`
    a.click()
    URL.revokeObjectURL(url)
}
</script>

<div class="w-full overflow-x-auto">
    <table class="w-full border-collapse">
        <thead>
            <tr>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Date</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Map</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Matchup</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Players</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Duration</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Region</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Winner</th>
                <th class="bg-gray-100 font-semibold p-3 text-left border-b border-gray-200 sticky top-0">Actions</th>
            </tr>
        </thead>
        <tbody>
            {#each sorted_replays as replay (replay.md5)}
                <tr class="hover:bg-gray-50">
                    <td class="p-3 border-b border-gray-100">{format_date(replay.played_timestamp)}</td>
                    <td class="p-3 border-b border-gray-100 max-w-48 truncate">{replay.map_name}</td>
                    <td class="p-3 border-b border-gray-100 font-semibold">{get_matchup(replay)}</td>
                    <td class="p-3 border-b border-gray-100">{get_players(replay)}</td>
                    <td class="p-3 border-b border-gray-100">{format_duration(replay.game_length_seconds)}</td>
                    <td class="p-3 border-b border-gray-100">{replay.region_short.toUpperCase()}</td>
                    <td class="p-3 border-b border-gray-100 font-semibold">{get_winner_display(replay)}</td>
                    <td class="p-3 border-b border-gray-100">
                        <button
                            class="btn-secondary mr-2"
                            onclick={() => download_replay(replay)}
                        >
                            Download
                        </button>
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
