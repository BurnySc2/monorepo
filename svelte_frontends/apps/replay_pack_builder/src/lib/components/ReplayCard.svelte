<script lang="ts">
import { type ParsedReplayFile } from "$lib/replay_types"

interface Props {
    replay: ParsedReplayFile
    show_remove?: boolean
    on_remove?: (md5: string) => void
}

let { replay, show_remove = true, on_remove }: Props = $props()

function format_date(timestamp: number): string {
    return new Date(timestamp).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}

function format_duration(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs.toString().padStart(2, "0")}s`
}

let matchup: string = $derived(() => {
    if (replay.teams.length !== 2) {
        return "N/A"
    }
    const players = replay.teams.flatMap((t) => t.players)
    if (players.length !== 2) {
        return "N/A"
    }
    return `${players[0].play_race[0]}v${players[1].play_race[0]}`
})

let teams_display: { result: string; players: { name: string; race: string; mmr: number }[] }[] = $derived(
    replay.teams.map((team) => ({
        result: team.result,
        players: team.players.map((p) => ({
            name: p.name,
            race: p.play_race,
            mmr: p.mmr,
        })),
    })),
)
</script>

<div class="replay-card">
    <div class="card-header">
        <h4 class="map-name">{replay.map_name}</h4>
        {#if show_remove && on_remove}
            <button
                class="remove-btn"
                onclick={() => on_remove?.(replay.md5)}
            >
                Remove
            </button>
        {/if}
    </div>

    <div class="card-meta">
        <span class="meta-item">
            <span class="meta-label">Date:</span>
            {format_date(replay.played_timestamp)}
        </span>
        <span class="meta-item">
            <span class="meta-label">Duration:</span>
            {format_duration(replay.game_length_seconds)}
        </span>
        <span class="meta-item">
            <span class="meta-label">Region:</span>
            {replay.region_short.toUpperCase()}
        </span>
        <span class="meta-item">
            <span class="meta-label">Expansion:</span>
            {replay.expansion}
        </span>
        <span class="meta-item matchup">
            <span class="meta-label">Matchup:</span>
            {matchup}
        </span>
    </div>

    <div class="teams">
        {#each teams_display as team, team_idx}
            <div
                class="team"
                class:winner={team.result === "Win"}
            >
                <span class="team-result">{team.result}</span>
                {#each team.players as player}
                    <div class="player">
                        <span class="player-name">{player.name}</span>
                        <span class="player-race">{player.race}</span>
                        {#if player.mmr > 0}
                            <span class="player-mmr">{player.mmr} MMR</span>
                        {/if}
                    </div>
                {/each}
            </div>
        {/each}
    </div>
</div>

<style>
.replay-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    background: #fff;
    transition: box-shadow 0.2s ease;
}

.replay-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.75rem;
}

.map-name {
    margin: 0;
    font-size: 1.1rem;
    color: #333;
}

.remove-btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.8rem;
    background: #fee2e2;
    color: #dc2626;
    border: 1px solid #fecaca;
    border-radius: 4px;
    cursor: pointer;
}

.remove-btn:hover {
    background: #fecaca;
}

.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #666;
}

.meta-item {
    display: flex;
    gap: 0.25rem;
}

.meta-label {
    color: #888;
}

.matchup {
    font-weight: 600;
    color: #333;
}

.teams {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.team {
    flex: 1;
    min-width: 150px;
    padding: 0.5rem;
    border-radius: 4px;
    background: #f9f9f9;
}

.team.winner {
    background: #dcfce7;
    border: 1px solid #bbf7d0;
}

.team-result {
    display: block;
    font-weight: 600;
    font-size: 0.85rem;
    color: #333;
    margin-bottom: 0.25rem;
}

.team.winner .team-result {
    color: #16a34a;
}

.player {
    display: flex;
    gap: 0.5rem;
    font-size: 0.85rem;
    align-items: center;
}

.player-name {
    color: #333;
}

.player-race {
    color: #666;
}

.player-mmr {
    color: #888;
    font-size: 0.8rem;
}
</style>
