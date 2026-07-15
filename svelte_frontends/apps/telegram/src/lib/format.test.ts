import { describe, expect, it } from "vitest"
import { format_duration, format_file_size } from "./format"

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
