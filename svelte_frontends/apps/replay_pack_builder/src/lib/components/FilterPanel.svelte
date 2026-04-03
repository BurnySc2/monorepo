<script lang="ts">
import { type FilterSettings, get_default_filter_settings, type ParsedReplayFile } from "$lib/replay_types"

interface Props {
    filter_settings: FilterSettings
    replays: ParsedReplayFile[]
    on_change: () => void
}

let { filter_settings = $bindable(get_default_filter_settings()), replays, on_change }: Props = $props()

function handle_change() {
    on_change()
}
</script>

<div class="filter-panel">
    <h3>Filters</h3>

    <label class="checkbox-label">
        <input
            type="checkbox"
            bind:checked={filter_settings.filter_enabled}
            onchange={handle_change}
        >
        Filter enabled
    </label>

    <fieldset>
        <legend>Game types</legend>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.game_matchmaking}
                onchange={handle_change}
            >
            Matchmaking
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.game_custom}
                onchange={handle_change}
            >
            Custom Game
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.game_include_games_with_ai}
                onchange={handle_change}
            >
            Include Games with AI
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.game_include_games_resumed_from_replay}
                onchange={handle_change}
            >
            Include Games Resumed from Replay
        </label>
    </fieldset>

    <fieldset>
        <legend>Expansion</legend>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_wol}
                onchange={handle_change}
            >
            Wings of Liberty
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_hots}
                onchange={handle_change}
            >
            Heart of the Swarm
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.expansion_lotv}
                onchange={handle_change}
            >
            Legacy of the Void
        </label>
    </fieldset>

    <fieldset>
        <legend>Server</legend>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.server_americas}
                onchange={handle_change}
            >
            Americas
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.server_europe}
                onchange={handle_change}
            >
            Europe
        </label>
        <label class="checkbox-label">
            <input
                type="checkbox"
                bind:checked={filter_settings.server_asia}
                onchange={handle_change}
            >
            Asia
        </label>
    </fieldset>

    <fieldset>
        <legend>Date played</legend>
        <div class="range-inputs">
            <label>
                From
                <input
                    type="date"
                    bind:value={filter_settings.date_played_min}
                    onchange={handle_change}
                >
            </label>
            <label>
                To
                <input
                    type="date"
                    bind:value={filter_settings.date_played_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset>
        <legend>Game duration (seconds)</legend>
        <div class="range-inputs">
            <label>
                Min
                <input
                    type="number"
                    bind:value={filter_settings.game_duration_min}
                    onchange={handle_change}
                >
            </label>
            <label>
                Max
                <input
                    type="number"
                    bind:value={filter_settings.game_duration_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset>
        <legend>Player count</legend>
        <div class="range-inputs">
            <label>
                Min
                <input
                    type="number"
                    bind:value={filter_settings.player_count_min}
                    onchange={handle_change}
                >
            </label>
            <label>
                Max
                <input
                    type="number"
                    bind:value={filter_settings.player_count_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset>
        <legend>Average player MMR</legend>
        <div class="range-inputs">
            <label>
                Min
                <input
                    type="number"
                    bind:value={filter_settings.average_mmr_min}
                    onchange={handle_change}
                >
            </label>
            <label>
                Max
                <input
                    type="number"
                    bind:value={filter_settings.average_mmr_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset>
        <legend>Matchups</legend>
        <div class="checkbox-grid">
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvp}
                    onchange={handle_change}
                >
                PvP
            </label>
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvt}
                    onchange={handle_change}
                >
                PvT
            </label>
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_pvz}
                    onchange={handle_change}
                >
                PvZ
            </label>
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_tvt}
                    onchange={handle_change}
                >
                TvT
            </label>
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_tvz}
                    onchange={handle_change}
                >
                TvZ
            </label>
            <label class="checkbox-label">
                <input
                    type="checkbox"
                    bind:checked={filter_settings.matchup_zvz}
                    onchange={handle_change}
                >
                ZvZ
            </label>
        </div>
    </fieldset>

    <fieldset>
        <legend>Player name (partial match, case insensitive)</legend>
        <label class="text-label">
            Must include
            <input
                type="text"
                bind:value={filter_settings.player_name_must_include}
                onchange={handle_change}
                placeholder="e.g., Hero, Burny"
            >
        </label>
        <label class="text-label">
            Must exclude
            <input
                type="text"
                bind:value={filter_settings.player_name_must_exclude}
                onchange={handle_change}
                placeholder="e.g., Computer"
            >
        </label>
    </fieldset>

    <fieldset>
        <legend>Map name (partial match, case insensitive)</legend>
        <label class="text-label">
            Must include
            <input
                type="text"
                bind:value={filter_settings.map_name_must_include}
                onchange={handle_change}
                placeholder="e.g., LE, Station"
            >
        </label>
        <label class="text-label">
            Must exclude
            <input
                type="text"
                bind:value={filter_settings.map_name_must_exclude}
                onchange={handle_change}
                placeholder="e.g., Altitude"
            >
        </label>
    </fieldset>
</div>

<style>
.filter-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

h3 {
    margin: 0;
    font-size: 1.1rem;
}

fieldset {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.75rem;
    margin: 0;
}

legend {
    font-weight: 600;
    padding: 0 0.5rem;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    margin-bottom: 0.25rem;
}

.checkbox-label:last-child {
    margin-bottom: 0;
}

.text-label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-bottom: 0.5rem;
}

.text-label:last-child {
    margin-bottom: 0;
}

.text-label input {
    padding: 0.25rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
}

.range-inputs {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}

.range-inputs label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    flex: 1;
    min-width: 100px;
}

.range-inputs input {
    padding: 0.25rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.9rem;
}

.checkbox-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
}

@media (max-width: 600px) {
    .checkbox-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .range-inputs {
        flex-direction: column;
    }
}
</style>
