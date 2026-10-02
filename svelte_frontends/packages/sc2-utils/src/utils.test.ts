import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import type { IGameData, IUiData } from "./types.js"
import {
    format_time,
    game_response_races,
    get_current_scene,
    get_scene_change,
    is_nephest_response,
    parse_poll_frequency,
    text_to_build_order,
    time_string_to_number,
    to_nephest_race,
    to_nephest_server,
    validate_game_from_game_data,
} from "./utils.js"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

const createGameData = (overrides: Partial<IGameData> = {}): IGameData => ({
    isReplay: false,
    displayTime: 0,
    players: [
        { id: 1, name: "Player1", type: "user", race: "Terr", result: "winidk" },
        { id: 2, name: "Player2", type: "user", race: "Prot", result: "lossidk" },
    ],
    ...overrides,
})

const createUiData = (overrides: Partial<IUiData> = {}): IUiData => ({
    activeScreens: [],
    ...overrides,
})

describe("validate_game_from_game_data", () => {
    it("returns '1v1' when there are 2 players", () => {
        const gameData = createGameData()
        expect(validate_game_from_game_data(gameData)).toBe("1v1")
    })

    it("returns 'other' when there are not 2 players", () => {
        const gameData = createGameData({
            players: [{ id: 1, name: "Solo", type: "user", race: "Terr", result: "winidk" }],
        })
        expect(validate_game_from_game_data(gameData)).toBe("other")
    })

    it("returns 'other' when there are 3 players", () => {
        const gameData = createGameData({
            players: [
                { id: 1, name: "P1", type: "user", race: "Terr", result: "winidk" },
                { id: 2, name: "P2", type: "user", race: "Prot", result: "lossidk" },
                { id: 3, name: "P3", type: "user", race: "Zerg", result: "lossidk" },
            ],
        })
        expect(validate_game_from_game_data(gameData)).toBe("other")
    })
})

describe("get_current_scene", () => {
    it("returns 'game' when no active screens and not replay", () => {
        const gameData = createGameData({ isReplay: false })
        const uiData = createUiData({ activeScreens: [] })
        expect(get_current_scene(gameData, uiData)).toBe("game")
    })

    it("returns 'replay' when no active screens and is replay", () => {
        const gameData = createGameData({ isReplay: true })
        const uiData = createUiData({ activeScreens: [] })
        expect(get_current_scene(gameData, uiData)).toBe("replay")
    })

    it("returns 'loading' when ScreenLoading is active", () => {
        const gameData = createGameData()
        const uiData = createUiData({ activeScreens: ["ScreenLoading/ScreenLoading"] })
        expect(get_current_scene(gameData, uiData)).toBe("loading")
    })

    it("returns 'menu' when other screens are active", () => {
        const gameData = createGameData()
        const uiData = createUiData({ activeScreens: ["ScreenGameMode"] })
        expect(get_current_scene(gameData, uiData)).toBe("menu")
    })
})

describe("get_scene_change", () => {
    it("returns 'noChange' when scenes are the same", () => {
        expect(get_scene_change("game", "game", true)).toBe("noChange")
        expect(get_scene_change("menu", "menu", true)).toBe("noChange")
    })

    it("returns 'toNewGameFromMenu' when going from menu to game with player", () => {
        expect(get_scene_change("menu", "game", true)).toBe("toNewGameFromMenu")
        expect(get_scene_change("unknown", "game", true)).toBe("toNewGameFromMenu")
    })

    it("returns 'toObserveGame' when going from menu to game without player", () => {
        expect(get_scene_change("menu", "game", false)).toBe("toObserveGame")
        expect(get_scene_change("unknown", "game", false)).toBe("toObserveGame")
    })

    it("returns 'toNewGameFromReplay' when going from replay to game", () => {
        expect(get_scene_change("replay", "game", true)).toBe("toNewGameFromReplay")
    })

    it("returns 'toReplayFromMenu' when going from menu to replay", () => {
        expect(get_scene_change("menu", "replay", true)).toBe("toReplayFromMenu")
        expect(get_scene_change("unknown", "replay", true)).toBe("toReplayFromMenu")
    })

    it("returns 'toReplayFromGame' when going from game to replay", () => {
        expect(get_scene_change("game", "replay", true)).toBe("toReplayFromGame")
    })

    it("returns 'toMenu' when going to menu", () => {
        expect(get_scene_change("game", "menu", true)).toBe("toMenu")
        expect(get_scene_change("replay", "menu", true)).toBe("toMenu")
    })

    it("returns 'noChange' when going to loading", () => {
        expect(get_scene_change("game", "loading", true)).toBe("noChange")
    })

    it("returns 'unknown' for other transitions", () => {
        expect(get_scene_change("game", "unknown", true)).toBe("unknown")
    })
})

describe("format_time", () => {
    it("formats seconds correctly", () => {
        expect(format_time(0)).toBe("0:00")
        expect(format_time(5)).toBe("0:05")
        expect(format_time(30)).toBe("0:30")
        expect(format_time(59)).toBe("0:59")
    })

    it("formats minutes and seconds correctly", () => {
        expect(format_time(60)).toBe("1:00")
        expect(format_time(90)).toBe("1:30")
        expect(format_time(125)).toBe("2:05")
        expect(format_time(600)).toBe("10:00")
        expect(format_time(3661)).toBe("61:01")
    })
})

describe("time_string_to_number", () => {
    it("converts time string to seconds", () => {
        expect(time_string_to_number("0:00")).toBe(0)
        expect(time_string_to_number("0:05")).toBe(5)
        expect(time_string_to_number("0:30")).toBe(30)
        expect(time_string_to_number("1:00")).toBe(60)
        expect(time_string_to_number("1:30")).toBe(90)
        expect(time_string_to_number("2:05")).toBe(125)
        expect(time_string_to_number("10:00")).toBe(600)
        expect(time_string_to_number("61:01")).toBe(3661)
    })
})

describe("text_to_build_order", () => {
    it("parses build order text correctly", () => {
        const text = "0:00 Opening\n0:30 Build stuff\n1:00 More stuff"
        const result = text_to_build_order(text)
        expect(result).toEqual([
            { time: 0, text: "Opening" },
            { time: 30, text: "Build stuff" },
            { time: 60, text: "More stuff" },
        ])
    })

    it("handles single line build order", () => {
        const text = "0:00 Single build"
        const result = text_to_build_order(text)
        expect(result).toEqual([{ time: 0, text: "Single build" }])
    })

    it("handles multiline but empty text", () => {
        const text = "0:00 \n0:30 Build"
        const result = text_to_build_order(text)
        expect(result).toEqual([
            { time: 0, text: "" },
            { time: 30, text: "Build" },
        ])
    })

    it("handles build order with multiple spaces in text", () => {
        const text = "0:00 First build line"
        const result = text_to_build_order(text)
        expect(result[0].text).toBe("First build line")
    })
})

describe("is_nephest_response", () => {
    it("returns true for valid Nephest response", () => {
        const response = {
            currentStats: { gamesPlayed: 10, rank: 1, rating: 1500 },
            previousStats: { gamesPlayed: 5, rank: 2, rating: 1400 },
            members: [
                {
                    terranGamesPlayed: 5,
                    protossGamesPlayed: 3,
                    zergGamesPlayed: 2,
                    randomGamesPlayed: 0,
                    account: { battleTag: "Player#1", id: 1, partition: "GLOBAL" },
                    character: {
                        accountId: 1,
                        battlenetId: 1,
                        clanId: 0,
                        name: "Player",
                        realm: 1,
                        region: "EU",
                    },
                    clan: {
                        activeMembers: 10,
                        avgLeagueType: 4,
                        avgRating: 1500,
                        games: 100,
                        id: 1,
                        members: 10,
                        name: "Clan",
                        region: "EU",
                        tag: "TAG",
                    },
                },
            ],
        }
        expect(is_nephest_response(response)).toBe(true)
    })

    it("returns false for invalid response", () => {
        expect(is_nephest_response(null)).toBe(false)
        expect(is_nephest_response({})).toBe(false)
        expect(is_nephest_response({ currentStats: {} })).toBe(false)
        expect(is_nephest_response({ members: [] })).toBe(false)
        expect(is_nephest_response("string")).toBe(false)
        expect(is_nephest_response(123)).toBe(false)
    })
})

describe("domain maps smoke", () => {
    it("maps representative entries", () => {
        expect(game_response_races.Terr).toBe("Terran")
        expect(to_nephest_race.Terran).toBe("terranGamesPlayed")
        expect(to_nephest_server.Europe).toBe("EU")
    })
})

describe("parse_poll_frequency", () => {
    it("returns 1000 for null and non-numeric input", () => {
        expect(parse_poll_frequency(null)).toBe(1000)
        expect(parse_poll_frequency("abc")).toBe(1000)
    })

    it("clamps values below 250 up to 250 and passes through larger values", () => {
        expect(parse_poll_frequency("100")).toBe(250)
        expect(parse_poll_frequency("500")).toBe(500)
        expect(parse_poll_frequency("1000")).toBe(1000)
    })
})

describe("poll frequency properties", () => {
    it("returns >=250 for numeric input else 1000", () => {
        fc.assert(
            fc.property(fc.integer({ min: -1000, max: 10000 }), (value) => {
                const result = parse_poll_frequency(String(value))
                expect(result).toBeGreaterThanOrEqual(250)
                if (value < 250) {
                    expect(result).toBe(250)
                } else {
                    expect(result).toBe(value)
                }
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })

    it("returns 1000 for null and non-numeric strings", () => {
        fc.assert(
            fc.property(fc.stringMatching(/^[^0-9-]+$/), (raw) => {
                if (raw.trim() === "") {
                    return
                }
                expect(parse_poll_frequency(raw)).toBe(1000)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("time round-trip properties", () => {
    it("format_time then time_string_to_number round-trips", () => {
        fc.assert(
            fc.property(fc.nat({ max: 7200 }), (seconds) => {
                const formatted = format_time(seconds)
                expect(time_string_to_number(formatted)).toBe(seconds)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("build order skip-invalid properties", () => {
    it("skips empty and invalid lines and never throws", () => {
        fc.assert(
            fc.property(fc.array(fc.string({ maxLength: 30 }), { maxLength: 10 }), (lines) => {
                const text = lines.join("\n")
                const result = text_to_build_order(text)
                expect(result.length).toBeLessThanOrEqual(lines.filter((line) => line.trim() !== "").length)
                for (const item of result) {
                    expect(Number.isFinite(item.time)).toBe(true)
                }
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })

    it("preserves valid m:ss lines", () => {
        fc.assert(
            fc.property(
                fc.array(fc.tuple(fc.nat({ max: 60 }), fc.nat({ max: 59 }), fc.stringMatching(/^[A-Za-z ]{1,10}$/)), {
                    minLength: 1,
                    maxLength: 5,
                }),
                (entries) => {
                    const text = entries
                        .map(([minutes, seconds, label]) => `${minutes}:${String(seconds).padStart(2, "0")} ${label}`)
                        .join("\n")
                    const result = text_to_build_order(text)
                    expect(result).toHaveLength(entries.length)
                },
            ),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
