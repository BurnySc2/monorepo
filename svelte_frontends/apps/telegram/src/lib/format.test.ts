import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import { format_duration, format_file_size } from "./format"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

function parse_formatted_size(formatted: string): { value: number; unit_index: number } {
    const sizes = ["B", "KB", "MB", "GB"]
    const [value_text, unit] = formatted.split(" ")
    return { value: Number(value_text), unit_index: sizes.indexOf(unit) }
}

describe("format_file_size", () => {
    it("returns 0 B for zero bytes", () => {
        expect(format_file_size(0)).toBe("0 B")
    })

    it("returns bytes for small values", () => {
        expect(format_file_size(500)).toBe("500 B")
        expect(format_file_size(1023)).toBe("1023 B")
    })

    it("returns KB for values in kilobyte range", () => {
        expect(format_file_size(1024)).toBe("1 KB")
        expect(format_file_size(1500)).toBe("1.5 KB")
        expect(format_file_size(10240)).toBe("10 KB")
    })

    it("returns MB for values in megabyte range", () => {
        expect(format_file_size(1048576)).toBe("1 MB")
        expect(format_file_size(5242880)).toBe("5 MB")
        expect(format_file_size(104857600)).toBe("100 MB")
    })

    it("returns GB for values in gigabyte range", () => {
        expect(format_file_size(1073741824)).toBe("1 GB")
        expect(format_file_size(2147483648)).toBe("2 GB")
    })
})

describe("format_duration", () => {
    it("returns empty string for zero", () => {
        expect(format_duration(0)).toBe("")
    })

    it("returns empty string for null/undefined", () => {
        expect(format_duration(null as unknown as number)).toBe("")
    })

    it("formats seconds only", () => {
        expect(format_duration(5)).toBe("0:05.000")
        expect(format_duration(30)).toBe("0:30.000")
        expect(format_duration(59)).toBe("0:59.000")
    })

    it("formats minutes and seconds", () => {
        expect(format_duration(60)).toBe("1:00.000")
        expect(format_duration(65)).toBe("1:05.000")
        expect(format_duration(125)).toBe("2:05.000")
        expect(format_duration(3599)).toBe("59:59.000")
    })

    it("formats hours, minutes, and seconds", () => {
        expect(format_duration(3600)).toBe("1:00:00.000")
        expect(format_duration(3661)).toBe("1:01:01.000")
        expect(format_duration(7200)).toBe("2:00:00.000")
        expect(format_duration(86399)).toBe("23:59:59.000")
    })

    it("formats milliseconds correctly", () => {
        expect(format_duration(46.185)).toBe("0:46.185")
        expect(format_duration(222.75999450684)).toBe("3:42.759")
        expect(format_duration(3661.5)).toBe("1:01:01.500")
        expect(format_duration(3723.5)).toBe("1:02:03.500")
    })
})

describe("format_duration properties", () => {
    it("is deterministic for same input", () => {
        fc.assert(
            fc.property(fc.double({ min: 0, max: 86400, noNaN: true }), (seconds) => {
                expect(format_duration(seconds)).toBe(format_duration(seconds))
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("format_file_size properties", () => {
    it("is monotonic in unit and value", () => {
        fc.assert(
            fc.property(fc.integer({ min: 0, max: 5000000000 }), fc.integer({ min: 0, max: 5000000000 }), (a, b) => {
                const [small, large] = a <= b ? [a, b] : [b, a]
                const parsed_small = parse_formatted_size(format_file_size(small))
                const parsed_large = parse_formatted_size(format_file_size(large))
                expect(parsed_small.unit_index).toBeLessThanOrEqual(parsed_large.unit_index)
                if (parsed_small.unit_index === parsed_large.unit_index) {
                    expect(parsed_small.value).toBeLessThanOrEqual(parsed_large.value)
                }
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
