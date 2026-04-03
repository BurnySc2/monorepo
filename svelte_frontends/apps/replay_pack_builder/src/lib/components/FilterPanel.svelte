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

<div class="flex flex-col gap-4">
    <h3 class="text-lg font-semibold m-0">Filters</h3>

    <label class="flex items-center gap-2 cursor-pointer mb-1">
        <input
            type="checkbox"
            class="checkbox"
            bind:checked={filter_settings.filter_enabled}
            onchange={handle_change}
        >
        Filter enabled
    </label>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Game types</legend>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.game_matchmaking}
                onchange={handle_change}
            >
            Matchmaking
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.game_custom}
                onchange={handle_change}
            >
            Custom Game
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.game_include_games_with_ai}
                onchange={handle_change}
            >
            Include Games with AI
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.game_include_games_resumed_from_replay}
                onchange={handle_change}
            >
            Include Games Resumed from Replay
        </label>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Expansion</legend>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.expansion_wol}
                onchange={handle_change}
            >
            Wings of Liberty
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.expansion_hots}
                onchange={handle_change}
            >
            Heart of the Swarm
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.expansion_lotv}
                onchange={handle_change}
            >
            Legacy of the Void
        </label>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Server</legend>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.server_americas}
                onchange={handle_change}
            >
            Americas
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.server_europe}
                onchange={handle_change}
            >
            Europe
        </label>
        <label class="flex items-center gap-2 cursor-pointer mb-1 last:mb-0">
            <input
                type="checkbox"
                class="checkbox"
                bind:checked={filter_settings.server_asia}
                onchange={handle_change}
            >
            Asia
        </label>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Date played</legend>
        <div class="flex gap-4 flex-wrap">
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                From
                <input
                    type="date"
                    class="input"
                    bind:value={filter_settings.date_played_min}
                    onchange={handle_change}
                >
            </label>
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                To
                <input
                    type="date"
                    class="input"
                    bind:value={filter_settings.date_played_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Game duration (seconds)</legend>
        <div class="flex gap-4 flex-wrap">
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Min
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.game_duration_min}
                    onchange={handle_change}
                >
            </label>
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Max
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.game_duration_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Player count</legend>
        <div class="flex gap-4 flex-wrap">
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Min
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.player_count_min}
                    onchange={handle_change}
                >
            </label>
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Max
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.player_count_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Average player MMR</legend>
        <div class="flex gap-4 flex-wrap">
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Min
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.average_mmr_min}
                    onchange={handle_change}
                >
            </label>
            <label class="flex flex-col gap-1 flex-1 min-w-24">
                Max
                <input
                    type="number"
                    class="input"
                    bind:value={filter_settings.average_mmr_max}
                    onchange={handle_change}
                >
            </label>
        </div>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Matchups</legend>
        <div class="grid grid-cols-3 gap-2">
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_pvp}
                    onchange={handle_change}
                >
                PvP
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_pvt}
                    onchange={handle_change}
                >
                PvT
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_pvz}
                    onchange={handle_change}
                >
                PvZ
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_tvt}
                    onchange={handle_change}
                >
                TvT
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_tvz}
                    onchange={handle_change}
                >
                TvZ
            </label>
            <label class="flex items-center gap-2 cursor-pointer">
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filter_settings.matchup_zvz}
                    onchange={handle_change}
                >
                ZvZ
            </label>
        </div>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Player name (partial match, case insensitive)</legend>
        <label class="flex flex-col gap-1 mb-2 last:mb-0">
            Must include
            <input
                type="text"
                class="input"
                bind:value={filter_settings.player_name_must_include}
                onchange={handle_change}
                placeholder="e.g., Hero, Burny"
            >
        </label>
        <label class="flex flex-col gap-1 mb-2 last:mb-0">
            Must exclude
            <input
                type="text"
                class="input"
                bind:value={filter_settings.player_name_must_exclude}
                onchange={handle_change}
                placeholder="e.g., Computer"
            >
        </label>
    </fieldset>

    <fieldset class="border border-gray-200 rounded p-3 m-0">
        <legend class="font-semibold px-2">Map name (partial match, case insensitive)</legend>
        <label class="flex flex-col gap-1 mb-2 last:mb-0">
            Must include
            <input
                type="text"
                class="input"
                bind:value={filter_settings.map_name_must_include}
                onchange={handle_change}
                placeholder="e.g., LE, Station"
            >
        </label>
        <label class="flex flex-col gap-1 mb-2 last:mb-0">
            Must exclude
            <input
                type="text"
                class="input"
                bind:value={filter_settings.map_name_must_exclude}
                onchange={handle_change}
                placeholder="e.g., Altitude"
            >
        </label>
    </fieldset>
</div>

<style>
@media (max-width: 600px) {
    .grid-cols-3 {
        grid-template-columns: repeat(2, 1fr);
    }
    .flex {
        flex-direction: column;
    }
}
</style>
