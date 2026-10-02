import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import { format_date_string, format_date_timestamp } from "./dates.js"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

const EN_US_DATE_PATTERN = /^[A-Z][a-z]{2} \d{1,2}, \d{4}$/

describe("format_date_timestamp", () => {
    it("formats Sep 30 2026 timestamp as en-US short date", () => {
        const local_noon = new Date(2026, 8, 30, 12, 0, 0)
        expect(format_date_timestamp(local_noon.getTime())).toBe("Sep 30, 2026")
    })

    it.each([
        Number.NaN,
        Number.POSITIVE_INFINITY,
        Number.NEGATIVE_INFINITY,
    ])("returns Invalid Date for non-finite timestamp %s", (timestamp) => {
        expect(format_date_timestamp(timestamp)).toBe("Invalid Date")
    })

    it("returns Invalid Date for out-of-range timestamp", () => {
        expect(format_date_timestamp(8.64e15 + 1000000)).toBe("Invalid Date")
    })
})

describe("format_date_string", () => {
    it("formats Sep 30 2026 date string as en-US short date", () => {
        expect(format_date_string("2026-09-30T12:00:00")).toBe("Sep 30, 2026")
    })

    it.each(["not-a-date", "", "invalid", "2026-13-45"])("returns Invalid Date for %s", (raw) => {
        expect(format_date_string(raw)).toBe("Invalid Date")
    })
})

describe("date format properties", () => {
    it("never throws and returns en-US pattern for finite 32-bit timestamps", () => {
        fc.assert(
            fc.property(fc.integer({ min: -2147483648, max: 2147483647 }), (timestamp) => {
                const result = format_date_timestamp(timestamp * 1000)
                expect(typeof result).toBe("string")
                expect(result === "Invalid Date" || EN_US_DATE_PATTERN.test(result)).toBe(true)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })

    it("never throws for arbitrary date strings", () => {
        fc.assert(
            fc.property(fc.string({ maxLength: 40 }), (raw) => {
                const result = format_date_string(raw)
                expect(typeof result).toBe("string")
                expect(result === "Invalid Date" || EN_US_DATE_PATTERN.test(result)).toBe(true)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
