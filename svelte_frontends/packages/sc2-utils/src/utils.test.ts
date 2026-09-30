import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import type { IGameData, IUiData } from "./types"
import {
    formatTime,
    gameResponseRaces,
    getCurrentScene,
    getSceneChange,
    isNephestResponse,
    parse_poll_frequency,
    textToBuildOrder,
    timeStringToNumber,
    toNephestRace,
    toNephestServer,
    validateGameFromGameData,
} from "./utils"

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

describe("validateGameFromGameData", () => {
    it("returns '1v1' when there are 2 players", () => {
        const gameData = createGameData()
        expect(validateGameFromGameData(gameData)).toBe("1v1")
    })

    it("returns 'other' when there are not 2 players", () => {
        const gameData = createGameData({
            players: [{ id: 1, name: "Solo", type: "user", race: "Terr", result: "winidk" }],
        })
        expect(validateGameFromGameData(gameData)).toBe("other")
    })

    it("returns 'other' when there are 3 players", () => {
        const gameData = createGameData({
            players: [
                { id: 1, name: "P1", type: "user", race: "Terr", result: "winidk" },
                { id: 2, name: "P2", type: "user", race: "Prot", result: "lossidk" },
                { id: 3, name: "P3", type: "user", race: "Zerg", result: "lossidk" },
            ],
        })
        expect(validateGameFromGameData(gameData)).toBe("other")
    })
})

describe("getCurrentScene", () => {
    it("returns 'game' when no active screens and not replay", () => {
        const gameData = createGameData({ isReplay: false })
        const uiData = createUiData({ activeScreens: [] })
        expect(getCurrentScene(gameData, uiData)).toBe("game")
    })

    it("returns 'replay' when no active screens and is replay", () => {
        const gameData = createGameData({ isReplay: true })
        const uiData = createUiData({ activeScreens: [] })
        expect(getCurrentScene(gameData, uiData)).toBe("replay")
    })

    it("returns 'loading' when ScreenLoading is active", () => {
        const gameData = createGameData()
        const uiData = createUiData({ activeScreens: ["ScreenLoading/ScreenLoading"] })
        expect(getCurrentScene(gameData, uiData)).toBe("loading")
    })

    it("returns 'menu' when other screens are active", () => {
        const gameData = createGameData()
        const uiData = createUiData({ activeScreens: ["ScreenGameMode"] })
        expect(getCurrentScene(gameData, uiData)).toBe("menu")
    })
})

describe("getSceneChange", () => {
    it("returns 'noChange' when scenes are the same", () => {
        expect(getSceneChange("game", "game", true)).toBe("noChange")
        expect(getSceneChange("menu", "menu", true)).toBe("noChange")
    })

    it("returns 'toNewGameFromMenu' when going from menu to game with player", () => {
        expect(getSceneChange("menu", "game", true)).toBe("toNewGameFromMenu")
        expect(getSceneChange("unknown", "game", true)).toBe("toNewGameFromMenu")
    })

    it("returns 'toObserveGame' when going from menu to game without player", () => {
        expect(getSceneChange("menu", "game", false)).toBe("toObserveGame")
        expect(getSceneChange("unknown", "game", false)).toBe("toObserveGame")
    })

    it("returns 'toNewGameFromReplay' when going from replay to game", () => {
        expect(getSceneChange("replay", "game", true)).toBe("toNewGameFromReplay")
    })

    it("returns 'toReplayFromMenu' when going from menu to replay", () => {
        expect(getSceneChange("menu", "replay", true)).toBe("toReplayFromMenu")
        expect(getSceneChange("unknown", "replay", true)).toBe("toReplayFromMenu")
    })

    it("returns 'toReplayFromGame' when going from game to replay", () => {
        expect(getSceneChange("game", "replay", true)).toBe("toReplayFromGame")
    })

    it("returns 'toMenu' when going to menu", () => {
        expect(getSceneChange("game", "menu", true)).toBe("toMenu")
        expect(getSceneChange("replay", "menu", true)).toBe("toMenu")
    })

    it("returns 'noChange' when going to loading", () => {
        expect(getSceneChange("game", "loading", true)).toBe("noChange")
    })

    it("returns 'unknown' for other transitions", () => {
        expect(getSceneChange("game", "unknown", true)).toBe("unknown")
    })
})

describe("formatTime", () => {
    it("formats seconds correctly", () => {
        expect(formatTime(0)).toBe("0:00")
        expect(formatTime(5)).toBe("0:05")
        expect(formatTime(30)).toBe("0:30")
        expect(formatTime(59)).toBe("0:59")
    })

    it("formats minutes and seconds correctly", () => {
        expect(formatTime(60)).toBe("1:00")
        expect(formatTime(90)).toBe("1:30")
        expect(formatTime(125)).toBe("2:05")
        expect(formatTime(600)).toBe("10:00")
        expect(formatTime(3661)).toBe("61:01")
    })
})

describe("timeStringToNumber", () => {
    it("converts time string to seconds", () => {
        expect(timeStringToNumber("0:00")).toBe(0)
        expect(timeStringToNumber("0:05")).toBe(5)
        expect(timeStringToNumber("0:30")).toBe(30)
        expect(timeStringToNumber("1:00")).toBe(60)
        expect(timeStringToNumber("1:30")).toBe(90)
        expect(timeStringToNumber("2:05")).toBe(125)
        expect(timeStringToNumber("10:00")).toBe(600)
        expect(timeStringToNumber("61:01")).toBe(3661)
    })
})

describe("textToBuildOrder", () => {
    it("parses build order text correctly", () => {
        const text = "0:00 Opening\n0:30 Build stuff\n1:00 More stuff"
        const result = textToBuildOrder(text)
        expect(result).toEqual([
            { time: 0, text: "Opening" },
            { time: 30, text: "Build stuff" },
            { time: 60, text: "More stuff" },
        ])
    })

    it("handles single line build order", () => {
        const text = "0:00 Single build"
        const result = textToBuildOrder(text)
        expect(result).toEqual([{ time: 0, text: "Single build" }])
    })

    it("handles multiline but empty text", () => {
        const text = "0:00 \n0:30 Build"
        const result = textToBuildOrder(text)
        expect(result).toEqual([
            { time: 0, text: "" },
            { time: 30, text: "Build" },
        ])
    })

    it("handles build order with multiple spaces in text", () => {
        const text = "0:00 First build line"
        const result = textToBuildOrder(text)
        expect(result[0].text).toBe("First build line")
    })
})

describe("isNephestResponse", () => {
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
        expect(isNephestResponse(response)).toBe(true)
    })

    it("returns false for invalid response", () => {
        expect(isNephestResponse(null)).toBe(false)
        expect(isNephestResponse({})).toBe(false)
        expect(isNephestResponse({ currentStats: {} })).toBe(false)
        expect(isNephestResponse({ members: [] })).toBe(false)
        expect(isNephestResponse("string")).toBe(false)
        expect(isNephestResponse(123)).toBe(false)
    })
})

describe("gameResponseRaces", () => {
    it("contains correct race mappings", () => {
        expect(gameResponseRaces.Terr).toBe("Terran")
        expect(gameResponseRaces.Prot).toBe("Protoss")
        expect(gameResponseRaces.Zerg).toBe("Zerg")
        expect(gameResponseRaces.random).toBe("Random")
    })
})

describe("toNephestRace", () => {
    it("contains correct race mappings", () => {
        expect(toNephestRace.Terran).toBe("terranGamesPlayed")
        expect(toNephestRace.Protoss).toBe("protossGamesPlayed")
        expect(toNephestRace.Zerg).toBe("zergGamesPlayed")
        expect(toNephestRace.random).toBe("randomGamesPlayed")
    })
})

describe("toNephestServer", () => {
    it("contains correct server mappings", () => {
        expect(toNephestServer.Europe).toBe("EU")
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
    it("formatTime then timeStringToNumber round-trips", () => {
        fc.assert(
            fc.property(fc.nat({ max: 7200 }), (seconds) => {
                const formatted = formatTime(seconds)
                expect(timeStringToNumber(formatted)).toBe(seconds)
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
                const result = textToBuildOrder(text)
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
                    const result = textToBuildOrder(text)
                    expect(result).toHaveLength(entries.length)
                },
            ),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
