import { describe, expect, it } from "vitest"
import {
    get_default_filter_settings,
    type ParsedReplayFile,
    rename_file_according_to_template,
    replay_passes_filter,
} from "./replay_types"

const create_replay = (overrides: Partial<ParsedReplayFile> = {}): ParsedReplayFile => ({
    user_id: "test_user",
    size: 1234,
    md5: "abc123",
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
                    name: "Opponent",
                    pick_race: "Zerg",
                    play_race: "Zerg",
                    is_human: true,
                    mmr: 400,
                },
            ],
        },
    ],
    played_timestamp: new Date("2024-06-15T14:30:00").getTime(),
    game_length_seconds: 600,
    map_name: "Cyber Forest LE",
    region_short: "us",
    expansion: "LotV",
    game_base_build: 12345,
    game_version: "5.0.14",
    game_type: "1v1",
    is_ladder: true,
    is_private: false,
    resume_from_replay: false,
    ...overrides,
})

describe("replay_passes_filter", () => {
    describe("filter_enabled", () => {
        it("returns true when filter is disabled", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), filter_enabled: false }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })

        it("applies filters when filter is enabled", () => {
            const replay = create_replay()
            const settings = get_default_filter_settings()
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("game type filters", () => {
        it("filters out ladder games when matchmaking is disabled", () => {
            const replay = create_replay({ is_ladder: true })
            const settings = { ...get_default_filter_settings(), game_matchmaking: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out custom games when custom game is disabled", () => {
            const replay = create_replay({ is_private: true })
            const settings = { ...get_default_filter_settings(), game_custom: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when game type matches enabled setting", () => {
            const replay = create_replay({ is_ladder: true })
            const settings = get_default_filter_settings()
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("AI player filter", () => {
        it("filters out games with AI players when disabled", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
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
                                name: "Computer",
                                pick_race: "Zerg",
                                play_race: "Zerg",
                                is_human: false,
                                mmr: null,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), game_include_games_with_ai: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes games with AI when AI filter is enabled", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
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
                                name: "Computer",
                                pick_race: "Zerg",
                                play_race: "Zerg",
                                is_human: false,
                                mmr: null,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), game_include_games_with_ai: true }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("expansion filter", () => {
        it("filters out WoL games when WoL is disabled", () => {
            const replay = create_replay({ expansion: "WoL" })
            const settings = { ...get_default_filter_settings(), expansion_wol: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out HotS games when HotS is disabled", () => {
            const replay = create_replay({ expansion: "HotS" })
            const settings = { ...get_default_filter_settings(), expansion_hots: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when expansion is enabled", () => {
            const replay = create_replay({ expansion: "LotV" })
            const settings = get_default_filter_settings()
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("server filter", () => {
        it("filters out US server when americas is disabled", () => {
            const replay = create_replay({ region_short: "us" })
            const settings = { ...get_default_filter_settings(), server_americas: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out EU server when europe is disabled", () => {
            const replay = create_replay({ region_short: "eu" })
            const settings = { ...get_default_filter_settings(), server_europe: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out KR server when asia is disabled", () => {
            const replay = create_replay({ region_short: "kr" })
            const settings = { ...get_default_filter_settings(), server_asia: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })

    describe("date filter", () => {
        it("filters out games before min date", () => {
            const replay = create_replay({ played_timestamp: new Date("2020-01-01").getTime() })
            const settings = {
                ...get_default_filter_settings(),
                date_played_min: new Date("2024-01-01").getTime(),
            }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out games after max date", () => {
            const replay = create_replay({ played_timestamp: new Date("2025-01-01").getTime() })
            const settings = {
                ...get_default_filter_settings(),
                date_played_max: new Date("2024-01-01").getTime(),
            }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })

    describe("duration filter", () => {
        it("filters out games shorter than min duration", () => {
            const replay = create_replay({ game_length_seconds: 60 })
            const settings = { ...get_default_filter_settings(), game_duration_min: 300 }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out games longer than max duration", () => {
            const replay = create_replay({ game_length_seconds: 1800 })
            const settings = { ...get_default_filter_settings(), game_duration_max: 1200 }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })

    describe("player count filter", () => {
        it("filters out games with too few players", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
                                name: "Solo",
                                pick_race: "Terran",
                                play_race: "Terran",
                                is_human: true,
                                mmr: 420,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), player_count_min: 2 }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })

    describe("MMR filter", () => {
        it("filters out games below min MMR", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
                                name: "BuRny",
                                pick_race: "Terran",
                                play_race: "Terran",
                                is_human: true,
                                mmr: 100,
                            },
                        ],
                    },
                    {
                        result: "Loss",
                        players: [
                            {
                                clan_tag: "",
                                name: "Opponent",
                                pick_race: "Zerg",
                                play_race: "Zerg",
                                is_human: true,
                                mmr: 100,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), average_mmr_min: 500 }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out games above max MMR", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
                                name: "BuRny",
                                pick_race: "Terran",
                                play_race: "Terran",
                                is_human: true,
                                mmr: 5000,
                            },
                        ],
                    },
                    {
                        result: "Loss",
                        players: [
                            {
                                clan_tag: "",
                                name: "Opponent",
                                pick_race: "Zerg",
                                play_race: "Zerg",
                                is_human: true,
                                mmr: 5000,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), average_mmr_max: 4000 }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })

    describe("matchup filter", () => {
        it("filters out PvP when PvP is disabled", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
                                name: "P1",
                                pick_race: "Protoss",
                                play_race: "Protoss",
                                is_human: true,
                                mmr: 500,
                            },
                        ],
                    },
                    {
                        result: "Loss",
                        players: [
                            {
                                clan_tag: "",
                                name: "P2",
                                pick_race: "Protoss",
                                play_race: "Protoss",
                                is_human: true,
                                mmr: 500,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), matchup_pvp: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("filters out TvZ when TvZ is disabled", () => {
            const replay = create_replay({
                teams: [
                    {
                        result: "Win",
                        players: [
                            {
                                clan_tag: "",
                                name: "P1",
                                pick_race: "Terran",
                                play_race: "Terran",
                                is_human: true,
                                mmr: 500,
                            },
                        ],
                    },
                    {
                        result: "Loss",
                        players: [
                            {
                                clan_tag: "",
                                name: "P2",
                                pick_race: "Zerg",
                                play_race: "Zerg",
                                is_human: true,
                                mmr: 500,
                            },
                        ],
                    },
                ],
            })
            const settings = { ...get_default_filter_settings(), matchup_tvz: false }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when matchup is enabled", () => {
            const replay = create_replay()
            const settings = get_default_filter_settings()
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("player name filter", () => {
        it("filters out when player name does not match must_include", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), player_name_must_include: "Hero" }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when player name matches must_include", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), player_name_must_include: "BuRny" }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })

        it("filters out when player name matches must_exclude", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), player_name_must_exclude: "Opponent" }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when no player names match must_exclude", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), player_name_must_exclude: "Computer" }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })

        it("handles multiple comma-separated names in must_include", () => {
            const replay = create_replay()
            const settings = { ...get_default_filter_settings(), player_name_must_include: "Bu,Other" }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })
    })

    describe("map name filter", () => {
        it("filters out when map name does not match must_include", () => {
            const replay = create_replay({ map_name: "Other Map" })
            const settings = { ...get_default_filter_settings(), map_name_must_include: "Cyber" }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })

        it("passes when map name matches must_include", () => {
            const replay = create_replay({ map_name: "Cyber Forest LE" })
            const settings = { ...get_default_filter_settings(), map_name_must_include: "Cyber" }
            expect(replay_passes_filter(replay, settings)).toBe(true)
        })

        it("filters out when map name matches must_exclude", () => {
            const replay = create_replay({ map_name: "Cyber Forest LE" })
            const settings = { ...get_default_filter_settings(), map_name_must_exclude: "Cyber" }
            expect(replay_passes_filter(replay, settings)).toBe(false)
        })
    })
})

describe("rename_file_according_to_template", () => {
    it("renames file with default pattern", () => {
        const replay = create_replay()
        const result = rename_file_according_to_template(
            replay,
            "{date}_{time}_{p1r}v{p2r}_{p1name}_vs_{p2name}_on_{map}",
        )
        expect(result).toBe("2024_06_15_14_30_00_TvZ_BuRny_vs_Opponent_on_Cyber_Forest_LE")
    })

    it("handles missing player names", () => {
        const replay = create_replay({
            teams: [
                {
                    result: "Win",
                    players: [
                        {
                            clan_tag: "",
                            name: "Solo",
                            pick_race: "Terran",
                            play_race: "Terran",
                            is_human: true,
                            mmr: 420,
                        },
                    ],
                },
                { result: "Loss", players: [] },
            ],
        })
        const result = rename_file_according_to_template(replay, "{p1name}_vs_{p2name}")
        expect(result).toBe("Solo_vs_")
    })

    it("replaces all placeholder occurrences", () => {
        const replay = create_replay()
        const result = rename_file_according_to_template(replay, "{map}_{map}_{map}")
        expect(result).toBe("Cyber_Forest_LE_Cyber_Forest_LE_Cyber_Forest_LE")
    })

    it("handles duration formatting", () => {
        const replay = create_replay({ game_length_seconds: 125 }) // 2m 5s
        const result = rename_file_according_to_template(replay, "{duration}")
        expect(result).toBe("2m 05s")
    })

    it("handles uppercase region", () => {
        const replay = create_replay({ region_short: "us" })
        const result = rename_file_according_to_template(replay, "{REGION}")
        expect(result).toBe("US")
    })

    it("handles race first letter placeholders", () => {
        const replay = create_replay({
            teams: [
                {
                    result: "Win",
                    players: [
                        {
                            clan_tag: "",
                            name: "P1",
                            pick_race: "Protoss",
                            play_race: "Protoss",
                            is_human: true,
                            mmr: 500,
                        },
                    ],
                },
                {
                    result: "Loss",
                    players: [
                        {
                            clan_tag: "",
                            name: "P2",
                            pick_race: "Terran",
                            play_race: "Terran",
                            is_human: true,
                            mmr: 500,
                        },
                    ],
                },
            ],
        })
        const result = rename_file_according_to_template(replay, "{p1r}v{p2r}")
        expect(result).toBe("PvT")
    })

    it("handles MMR placeholders", () => {
        const replay = create_replay({
            teams: [
                {
                    result: "Win",
                    players: [
                        {
                            clan_tag: "",
                            name: "P1",
                            pick_race: "Terran",
                            play_race: "Terran",
                            is_human: true,
                            mmr: 1234,
                        },
                    ],
                },
                {
                    result: "Loss",
                    players: [
                        { clan_tag: "", name: "P2", pick_race: "Zerg", play_race: "Zerg", is_human: true, mmr: 5678 },
                    ],
                },
            ],
        })
        const result = rename_file_according_to_template(replay, "{p1mmr}_{p2mmr}")
        expect(result).toBe("1234_5678")
    })

    it("handles version placeholder", () => {
        const replay = create_replay({ game_version: "5.0.14" })
        const result = rename_file_according_to_template(replay, "v{version}")
        expect(result).toBe("v5.0.14")
    })

    it("preserves text not in placeholders", () => {
        const replay = create_replay()
        const result = rename_file_according_to_template(replay, "SC2_{map}_Replay")
        expect(result).toBe("SC2_Cyber_Forest_LE_Replay")
    })
})
