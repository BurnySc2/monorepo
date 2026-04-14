import type {
    ParsedReplayFile as ApiParsedReplayFile,
    ReplayPlayer as ApiReplayPlayer,
    ReplayTeam as ApiReplayTeam,
} from "@repo/api-types"

// Re-export from api-types for external use
export type { ReplayPlayer, ReplayTeam } from "@repo/api-types"

// Client-side extended type (adds file_data and file_name)
export interface ParsedReplayFile extends ApiParsedReplayFile {
    file_data?: ArrayBuffer
    file_name?: string
}
export type Region = "us" | "eu" | "kr" | "cn"
export type Expansion = "WoL" | "HotS" | "LotV"
export type Result = "Win" | "Loss" | null

export interface FilterSettings {
    filter_enabled: boolean
    game_matchmaking: boolean
    game_custom: boolean
    game_coop: boolean
    game_arcade: boolean
    game_include_games_with_ai: boolean
    game_include_games_resumed_from_replay: boolean
    expansion_wol: boolean
    expansion_hots: boolean
    expansion_lotv: boolean
    server_americas: boolean
    server_europe: boolean
    server_asia: boolean
    date_played_min: number
    date_played_max: number
    game_duration_min: number
    game_duration_max: number
    player_count_min: number
    player_count_max: number
    average_mmr_min: number
    average_mmr_max: number
    matchup_pvp: boolean
    matchup_pvt: boolean
    matchup_pvz: boolean
    matchup_tvt: boolean
    matchup_tvz: boolean
    matchup_zvz: boolean
    player_name_must_include: string
    player_name_must_exclude: string
    map_name_must_include: string
    map_name_must_exclude: string
    replay_name_pattern: string
}

export const DEFAULT_REPLAY_NAME_PATTERN = "{date}_{time}_{p1r}v{p2r}_{p1name}_vs_{p2name}_on_{map}"

export function get_default_filter_settings(): FilterSettings {
    const now = Date.now()
    return {
        filter_enabled: true,
        game_matchmaking: true,
        game_custom: true,
        game_coop: true,
        game_arcade: true,
        game_include_games_with_ai: false,
        game_include_games_resumed_from_replay: false,
        expansion_wol: true,
        expansion_hots: true,
        expansion_lotv: true,
        server_americas: true,
        server_europe: true,
        server_asia: true,
        date_played_min: new Date("2010-01-01").getTime(),
        date_played_max: now,
        game_duration_min: 0,
        game_duration_max: 9999,
        player_count_min: 2,
        player_count_max: 2,
        average_mmr_min: 0,
        average_mmr_max: 9999,
        matchup_pvp: true,
        matchup_pvt: true,
        matchup_pvz: true,
        matchup_tvt: true,
        matchup_tvz: true,
        matchup_zvz: true,
        player_name_must_include: "",
        player_name_must_exclude: "",
        map_name_must_include: "",
        map_name_must_exclude: "",
        replay_name_pattern: DEFAULT_REPLAY_NAME_PATTERN,
    }
}

export function replay_passes_filter(replay: ParsedReplayFile, settings: FilterSettings): boolean {
    if (!settings.filter_enabled) {
        return true
    }

    // Game type filter
    if (!settings.game_matchmaking && replay.is_ladder) {
        return false
    }
    if (!settings.game_custom && replay.is_private) {
        return false
    }

    // AI players filter
    const has_computers = replay.teams.some((team) => team.players.some((player) => !player.is_human))
    if (!settings.game_include_games_with_ai && has_computers) {
        return false
    }

    // Resume from replay filter
    if (!settings.game_include_games_resumed_from_replay && replay.resume_from_replay) {
        return false
    }

    // Expansion filter
    if (!settings.expansion_wol && replay.expansion === "WoL") {
        return false
    }
    if (!settings.expansion_hots && replay.expansion === "HotS") {
        return false
    }
    if (!settings.expansion_lotv && replay.expansion === "LotV") {
        return false
    }

    // Server filter
    if (!settings.server_americas && replay.region_short === "us") {
        return false
    }
    if (!settings.server_europe && replay.region_short === "eu") {
        return false
    }
    if (!settings.server_asia && replay.region_short === "kr") {
        return false
    }

    // Date played filter - convert date strings to timestamps
    const date_played_min =
        typeof settings.date_played_min === "string"
            ? new Date(settings.date_played_min).getTime()
            : settings.date_played_min
    const date_played_max =
        typeof settings.date_played_max === "string"
            ? new Date(settings.date_played_max).getTime()
            : settings.date_played_max

    if (replay.played_timestamp < date_played_min || replay.played_timestamp > date_played_max) {
        return false
    }

    // Game duration filter
    if (
        replay.game_length_seconds < settings.game_duration_min ||
        replay.game_length_seconds > settings.game_duration_max
    ) {
        return false
    }

    // Player count filter
    const players_count = replay.teams.reduce((sum, team) => sum + team.players.length, 0)
    if (players_count < settings.player_count_min || players_count > settings.player_count_max) {
        return false
    }

    // Average MMR filter
    const all_mmrs = replay.teams
        .flatMap((team) => team.players)
        .map((p) => p.mmr)
        .filter((m) => m !== null) as number[]
    if (all_mmrs.length > 0) {
        const average_mmr = all_mmrs.reduce((a, b) => a + b, 0) / all_mmrs.length
        if (average_mmr < settings.average_mmr_min || average_mmr > settings.average_mmr_max) {
            return false
        }
    }

    // Matchup filter
    if (replay.teams.length === 2 && players_count === 2) {
        const players = [replay.teams[0].players[0], replay.teams[1].players[0]]
        const sorted_races = [...players].sort((a, b) => a.play_race.localeCompare(b.play_race))
        const player_races = `${sorted_races[0].play_race[0]}v${sorted_races[1].play_race[0]}`

        if (!settings.matchup_pvp && player_races === "PvP") {
            return false
        }
        if (!settings.matchup_pvt && player_races === "PvT") {
            return false
        }
        if (!settings.matchup_pvz && player_races === "PvZ") {
            return false
        }
        if (!settings.matchup_tvt && player_races === "TvT") {
            return false
        }
        if (!settings.matchup_tvz && player_races === "TvZ") {
            return false
        }
        if (!settings.matchup_zvz && player_races === "ZvZ") {
            return false
        }
    }

    // Player name filter
    const all_player_names = replay.teams.flatMap((team) => team.players).map((p) => p.name.toLowerCase())

    if (settings.player_name_must_include) {
        const include_list = settings.player_name_must_include
            .split(",")
            .map((s) => s.trim().toLowerCase())
            .filter((s) => s)
        if (include_list.length > 0) {
            const matches = all_player_names.some((name) => include_list.some((search) => name.includes(search)))
            if (!matches) {
                return false
            }
        }
    }

    if (settings.player_name_must_exclude) {
        const exclude_list = settings.player_name_must_exclude
            .split(",")
            .map((s) => s.trim().toLowerCase())
            .filter((s) => s)
        if (exclude_list.length > 0) {
            const matches = all_player_names.some((name) => exclude_list.some((search) => name.includes(search)))
            if (matches) {
                return false
            }
        }
    }

    // Map name filter
    const map_name = replay.map_name.toLowerCase()

    if (settings.map_name_must_include) {
        const include_list = settings.map_name_must_include
            .split(",")
            .map((s) => s.trim().toLowerCase())
            .filter((s) => s)
        if (include_list.length > 0) {
            const matches = include_list.some((search) => map_name.includes(search))
            if (!matches) {
                return false
            }
        }
    }

    if (settings.map_name_must_exclude) {
        const exclude_list = settings.map_name_must_exclude
            .split(",")
            .map((s) => s.trim().toLowerCase())
            .filter((s) => s)
        if (exclude_list.length > 0) {
            const matches = exclude_list.some((search) => map_name.includes(search))
            if (matches) {
                return false
            }
        }
    }

    return true
}

export function rename_file_according_to_template(replay: ParsedReplayFile, pattern: string): string {
    const player1 = replay.teams[0]?.players[0]
    const player2 = replay.teams[1]?.players[0]

    const date = new Date(replay.played_timestamp)
    const date_str = `${date.getFullYear()}_${String(date.getMonth() + 1).padStart(2, "0")}_${String(date.getDate()).padStart(2, "0")}`
    const time_str = `${String(date.getHours()).padStart(2, "0")}_${String(date.getMinutes()).padStart(2, "0")}_${String(date.getSeconds()).padStart(2, "0")}`

    const minutes = Math.floor(replay.game_length_seconds / 60)
    const seconds = replay.game_length_seconds % 60
    const duration = `${minutes}m ${seconds.toString().padStart(2, "0")}s`

    const map = replay.map_name.replace(/ /g, "_")
    const region = replay.region_short
    const version = replay.game_version

    const p1name = player1?.name || ""
    const p1race = player1?.play_race || " "
    const p1r = p1race[0] || " "
    const p1mmr = player1?.mmr ?? 0

    const p2name = player2?.name || ""
    const p2race = player2?.play_race || " "
    const p2r = p2race[0] || " "
    const p2mmr = player2?.mmr ?? 0

    const placeholders: Record<string, string | number> = {
        date: date_str,
        time: time_str,
        duration: duration,
        map: map,
        region: region,
        REGION: region.toUpperCase(),
        version: version,
        p1name: p1name,
        p1race: p1race,
        p1r: p1r,
        p1mmr: p1mmr,
        p2name: p2name,
        p2race: p2race,
        p2r: p2r,
        p2mmr: p2mmr,
    }

    let new_name = pattern
    for (const [placeholder, value] of Object.entries(placeholders)) {
        new_name = new_name.replace(new RegExp(`\\{${placeholder}\\}`, "g"), String(value))
    }

    return new_name
}
