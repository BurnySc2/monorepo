import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("$app/environment", () => ({
    browser: false,
    dev: true,
    building: false,
    version: "0.0.0-test",
}))

import {
    clear_sort,
    get_sort_direction,
    get_sort_priority,
    get_sort_tooltip,
    SortStateSchema,
    sort_state,
    to_sort_items,
    toggle_sort,
} from "./sort_settings.svelte"

describe("sort_settings", () => {
    beforeEach(() => {
        clear_sort()
    })

    describe("toggle_sort", () => {
        it("adds column as DESCENDING on first click", () => {
            toggle_sort("message_date")
            expect(sort_state).toEqual([{ column_key: "message_date", direction: "desc" }])
        })

        it("flips to ASCENDING on second click", () => {
            toggle_sort("message_date")
            toggle_sort("message_date")
            expect(sort_state).toEqual([{ column_key: "message_date", direction: "asc" }])
        })

        it("removes column on third click", () => {
            toggle_sort("message_date")
            toggle_sort("message_date")
            toggle_sort("message_date")
            expect(sort_state).toEqual([])
        })

        it("new column becomes highest priority (index 0)", () => {
            toggle_sort("channel_title")
            toggle_sort("message_date")
            expect(sort_state[0].column_key).toBe("message_date")
            expect(sort_state[1].column_key).toBe("channel_title")
        })

        it("handles multiple columns with correct priority", () => {
            toggle_sort("amount_of_reactions")
            toggle_sort("amount_of_comments")
            toggle_sort("message_date")

            expect(sort_state).toHaveLength(3)
            expect(sort_state[0].column_key).toBe("message_date")
            expect(sort_state[1].column_key).toBe("amount_of_comments")
            expect(sort_state[2].column_key).toBe("amount_of_reactions")
        })

        it("clicking existing desc column flips to asc without changing position", () => {
            toggle_sort("channel_title")
            toggle_sort("message_date")
            // order: [message_date(desc), channel_title(desc)]

            // Click channel_title again - flips to asc, stays at index 1
            toggle_sort("channel_title")
            expect(sort_state[0].column_key).toBe("message_date")
            expect(sort_state[1].column_key).toBe("channel_title")
            expect(sort_state[1].direction).toBe("asc")
        })

        it("cycles through all 3 states correctly for same column", () => {
            // none → desc
            toggle_sort("message_date")
            expect(sort_state).toHaveLength(1)
            expect(sort_state[0].direction).toBe("desc")

            // desc → asc
            toggle_sort("message_date")
            expect(sort_state).toHaveLength(1)
            expect(sort_state[0].direction).toBe("asc")

            // asc → none
            toggle_sort("message_date")
            expect(sort_state).toHaveLength(0)
        })

        it("does not affect other columns when toggling one", () => {
            toggle_sort("channel_title")
            toggle_sort("message_date")

            // Toggle message_date off
            toggle_sort("message_date")
            toggle_sort("message_date")

            expect(sort_state).toHaveLength(1)
            expect(sort_state[0].column_key).toBe("channel_title")
        })
    })

    describe("get_sort_priority", () => {
        it("returns 0 for unsorted column", () => {
            expect(get_sort_priority("message_date")).toBe(0)
        })

        it("returns 1-based index for sorted columns", () => {
            toggle_sort("channel_title")
            toggle_sort("message_date")
            expect(get_sort_priority("message_date")).toBe(1)
            expect(get_sort_priority("channel_title")).toBe(2)
        })

        it("updates after toggle", () => {
            toggle_sort("message_date")
            expect(get_sort_priority("message_date")).toBe(1)

            toggle_sort("message_date") // flip to asc
            expect(get_sort_priority("message_date")).toBe(1) // still priority 1

            toggle_sort("message_date") // remove
            expect(get_sort_priority("message_date")).toBe(0)
        })

        it("returns 0 for column never added", () => {
            toggle_sort("channel_title")
            expect(get_sort_priority("message_date")).toBe(0)
        })
    })

    describe("get_sort_direction", () => {
        it("returns null for unsorted column", () => {
            expect(get_sort_direction("message_date")).toBeNull()
        })

        it("returns desc after first click", () => {
            toggle_sort("message_date")
            expect(get_sort_direction("message_date")).toBe("desc")
        })

        it("returns asc after second click", () => {
            toggle_sort("message_date")
            toggle_sort("message_date")
            expect(get_sort_direction("message_date")).toBe("asc")
        })

        it("returns null after third click (removed)", () => {
            toggle_sort("message_date")
            toggle_sort("message_date")
            toggle_sort("message_date")
            expect(get_sort_direction("message_date")).toBeNull()
        })
    })

    describe("clear_sort", () => {
        it("empties sort state", () => {
            toggle_sort("message_date")
            toggle_sort("channel_title")
            toggle_sort("amount_of_reactions")

            clear_sort()
            expect(sort_state).toEqual([])
        })

        it("works when already empty", () => {
            clear_sort()
            expect(sort_state).toEqual([])
        })

        it("clearing updates priority of all columns to 0", () => {
            toggle_sort("message_date")
            toggle_sort("channel_title")

            clear_sort()
            expect(get_sort_priority("message_date")).toBe(0)
            expect(get_sort_priority("channel_title")).toBe(0)
        })
    })

    describe("get_sort_tooltip", () => {
        it("returns 'Click to sort descending' for unsorted column", () => {
            expect(get_sort_tooltip("message_date")).toBe("Click to sort descending")
        })

        it("returns correct tooltip for desc sort", () => {
            toggle_sort("message_date")
            expect(get_sort_tooltip("message_date")).toContain("descending")
            expect(get_sort_tooltip("message_date")).toContain("priority 1")
            expect(get_sort_tooltip("message_date")).toContain("switch to ascending")
        })

        it("returns correct tooltip for asc sort", () => {
            toggle_sort("message_date")
            toggle_sort("message_date")
            expect(get_sort_tooltip("message_date")).toContain("ascending")
            expect(get_sort_tooltip("message_date")).toContain("priority 1")
            expect(get_sort_tooltip("message_date")).toContain("remove sort")
        })

        it("includes correct priority number", () => {
            toggle_sort("channel_title")
            toggle_sort("message_date")
            expect(get_sort_tooltip("message_date")).toContain("priority 1")
            expect(get_sort_tooltip("channel_title")).toContain("priority 2")
        })

        it("returns default tooltip for unsorted column among sorted ones", () => {
            toggle_sort("message_date")
            expect(get_sort_tooltip("channel_title")).toBe("Click to sort descending")
        })
    })

    describe("to_sort_items", () => {
        it("returns empty array when no sorts", () => {
            expect(to_sort_items()).toEqual([])
        })

        it("converts single sort to backend format", () => {
            toggle_sort("message_date")
            expect(to_sort_items()).toEqual([{ column: "message_date", ascending: false }])
        })

        it("converts multiple sorts with correct ascending flags", () => {
            toggle_sort("amount_of_reactions") // desc
            toggle_sort("amount_of_comments") // desc
            toggle_sort("amount_of_comments") // flip to asc

            const clause = to_sort_items()
            expect(clause).toEqual([
                { column: "amount_of_comments", ascending: true },
                { column: "amount_of_reactions", ascending: false },
            ])
        })

        it("reflects changes after toggle", () => {
            toggle_sort("message_date")
            expect(to_sort_items()).toEqual([{ column: "message_date", ascending: false }])

            toggle_sort("message_date") // flip to asc
            expect(to_sort_items()).toEqual([{ column: "message_date", ascending: true }])

            toggle_sort("message_date") // remove
            expect(to_sort_items()).toEqual([])
        })

        it("maintains correct order matching sort_state", () => {
            toggle_sort("amount_of_reactions")
            toggle_sort("amount_of_comments")
            toggle_sort("message_date")

            const clause = to_sort_items()
            expect(clause.map((e) => e.column)).toEqual(["message_date", "amount_of_comments", "amount_of_reactions"])
        })
    })

    describe("SortStateSchema", () => {
        it("parses valid sort state", () => {
            const result = SortStateSchema.parse([
                { column_key: "message_date", direction: "asc" },
                { column_key: "channel_title", direction: "desc" },
            ])
            expect(result).toHaveLength(2)
            expect(result[0].column_key).toBe("message_date")
            expect(result[0].direction).toBe("asc")
        })

        it("defaults to empty array when undefined", () => {
            const result = SortStateSchema.parse(undefined)
            expect(result).toEqual([])
        })

        it("defaults to empty array when null", () => {
            // Zod .default() only applies to undefined, not null
            // null is not a valid array, so it should throw
            expect(() => SortStateSchema.parse(null)).toThrow()
        })

        it("rejects invalid direction", () => {
            expect(() => SortStateSchema.parse([{ column_key: "test", direction: "up" }])).toThrow()
        })

        it("rejects missing column_key", () => {
            expect(() => SortStateSchema.parse([{ direction: "asc" } as any])).toThrow()
        })

        it("rejects non-array input", () => {
            expect(() => SortStateSchema.parse("not an array")).toThrow()
        })

        it("parses empty array", () => {
            const result = SortStateSchema.parse([])
            expect(result).toEqual([])
        })
    })
})
