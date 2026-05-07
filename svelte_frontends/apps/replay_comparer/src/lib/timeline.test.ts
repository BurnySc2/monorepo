import { describe, expect, it } from "vitest"
import {
    gameloop_to_time_string,
    is_event_timeline,
    is_spending_option,
    merge_timelines,
    sort_by_key,
} from "./timeline"
import { EVENT_TIMELINE_OPTIONS, SPENDING_OPTIONS, TIMELINE_OPTIONS, type TimelineData } from "./types"

const createTimelineData = (overrides: Partial<TimelineData> = {}): TimelineData => ({
    gameloop: 0,
    workers_active: 12,
    workers_produced: 12,
    workers_lost: 0,
    supply: 13,
    supply_cap: 15,
    supply_block: 0,
    spm: 0,
    total_army_value: 0,
    total_resources_lost: 0,
    total_resources_collected: 200,
    workers_killed: 0,
    resource_collection_rate_all: 200,
    army_lost: 0,
    active_army: 0,
    buildings_started: 1,
    building_count: 1,
    upgrades_completed: 0,
    spending_econ: 100,
    spending_tech: 0,
    spending_army: 0,
    spending_total: 100,
    unit_count: 0,
    ...overrides,
})

describe("sort_by_key", () => {
    it("sorts array by numeric key in ascending order", () => {
        const arr = [
            { gameloop: 448, value: 3 },
            { gameloop: 0, value: 1 },
            { gameloop: 224, value: 2 },
        ]
        sort_by_key(arr, "gameloop")
        expect(arr.map((a) => a.gameloop)).toEqual([0, 224, 448])
    })

    it("sorts in place and modifies original array", () => {
        const arr = [
            { id: 3, name: "c" },
            { id: 1, name: "a" },
            { id: 2, name: "b" },
        ]
        const result = sort_by_key(arr, "id")
        expect(arr[0].id).toBe(1)
        expect(result).toBeUndefined()
    })
})

describe("gameloop_to_time_string", () => {
    it("converts gameloop 0 to 0:00", () => {
        expect(gameloop_to_time_string(0)).toBe("0:00")
    })

    it("converts gameloop 224 to 0:10", () => {
        expect(gameloop_to_time_string(224)).toBe("0:10")
    })

    it("converts gameloop 2240 to 1:40", () => {
        expect(gameloop_to_time_string(2240)).toBe("1:40")
    })

    it("pads seconds with leading zero", () => {
        expect(gameloop_to_time_string(112)).toBe("0:05")
    })

    it("handles large gameloops", () => {
        expect(gameloop_to_time_string(22400)).toBe("16:40")
    })
})

describe("is_event_timeline", () => {
    it("returns true for buildings_started", () => {
        expect(is_event_timeline("buildings_started")).toBe(true)
    })

    it("returns true for upgrades_completed", () => {
        expect(is_event_timeline("upgrades_completed")).toBe(true)
    })

    it("returns false for workers_active", () => {
        expect(is_event_timeline("workers_active")).toBe(false)
    })

    it("returns false for spending_econ", () => {
        expect(is_event_timeline("spending_econ")).toBe(false)
    })

    it.each(EVENT_TIMELINE_OPTIONS)("returns true for %s", (option) => {
        expect(is_event_timeline(option)).toBe(true)
    })

    it.each(
        TIMELINE_OPTIONS.filter((o) => !EVENT_TIMELINE_OPTIONS.includes(o as (typeof EVENT_TIMELINE_OPTIONS)[number])),
    )("returns false for non-event options like %s", (option) => {
        expect(is_event_timeline(option)).toBe(false)
    })
})

describe("is_spending_option", () => {
    it("returns true for spending_econ", () => {
        expect(is_spending_option("spending_econ")).toBe(true)
    })

    it("returns true for spending_tech", () => {
        expect(is_spending_option("spending_tech")).toBe(true)
    })

    it("returns true for spending_army", () => {
        expect(is_spending_option("spending_army")).toBe(true)
    })

    it("returns false for workers_active", () => {
        expect(is_spending_option("workers_active")).toBe(false)
    })

    it("returns false for buildings_started", () => {
        expect(is_spending_option("buildings_started")).toBe(false)
    })

    it.each(SPENDING_OPTIONS)("returns true for %s", (option) => {
        expect(is_spending_option(option)).toBe(true)
    })

    it.each(
        TIMELINE_OPTIONS.filter((o) => !SPENDING_OPTIONS.includes(o as (typeof SPENDING_OPTIONS)[number])),
    )("returns false for non-spending options like %s", (option) => {
        expect(is_spending_option(option)).toBe(false)
    })
})

describe("merge_timelines", () => {
    it("merges timelines with correct interleaving by gameloop", () => {
        const realTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 12 }),
                createTimelineData({ gameloop: 0, workers_active: 14 }),
            ],
            [
                createTimelineData({ gameloop: 224, workers_active: 16 }),
                createTimelineData({ gameloop: 224, workers_active: 18 }),
            ],
        ]
        const idealTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 13 }),
                createTimelineData({ gameloop: 0, workers_active: 15 }),
            ],
            [
                createTimelineData({ gameloop: 224, workers_active: 17 }),
                createTimelineData({ gameloop: 224, workers_active: 19 }),
            ],
        ]

        const result = merge_timelines(realTimeline, idealTimeline, 1, 1)

        expect(result.length).toBe(4)
        expect(result[0][1].gameloop).toBe(0)
        expect(result[1][1].gameloop).toBe(0)
        expect(result[2][1].gameloop).toBe(224)
        expect(result[3][1].gameloop).toBe(224)
    })

    it("handles different player selections", () => {
        const realTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 12 }),
                createTimelineData({ gameloop: 0, workers_active: 100 }),
            ],
        ]
        const idealTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 13 }),
                createTimelineData({ gameloop: 0, workers_active: 200 }),
            ],
        ]

        const result = merge_timelines(realTimeline, idealTimeline, 0, 1)

        expect(result[0][1].workers_active).toBe(12)
        expect(result[0][2].workers_active).toBe(200)
    })

    it("maintains running state for each player", () => {
        const realTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 12 }),
                createTimelineData({ gameloop: 0, workers_active: 20 }),
            ],
            [
                createTimelineData({ gameloop: 448, workers_active: 16 }),
                createTimelineData({ gameloop: 448, workers_active: 24 }),
            ],
        ]
        const idealTimeline: TimelineData[][] = [
            [
                createTimelineData({ gameloop: 0, workers_active: 13 }),
                createTimelineData({ gameloop: 0, workers_active: 21 }),
            ],
            [
                createTimelineData({ gameloop: 448, workers_active: 17 }),
                createTimelineData({ gameloop: 448, workers_active: 25 }),
            ],
        ]

        const result = merge_timelines(realTimeline, idealTimeline, 0, 0)

        expect(result[0][1].workers_active).toBe(12)
        expect(result[1][1].workers_active).toBe(12)
        expect(result[2][1].workers_active).toBe(16)
        expect(result[3][1].workers_active).toBe(16)
    })
})
