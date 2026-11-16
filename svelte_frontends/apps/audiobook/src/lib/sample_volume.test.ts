import { describe, expect, it } from "vitest"
import { clamp_volume_percent, clamp_volume_ratio } from "./sample_volume"

describe("sample_volume", () => {
    it("keeps boundaries 0 and 100", () => {
        expect(clamp_volume_percent(0)).toBe(0)
        expect(clamp_volume_percent(100)).toBe(100)
        expect(clamp_volume_ratio(0)).toBe(0)
        expect(clamp_volume_ratio(100)).toBe(1)
    })

    it("clamps out-of-bounds values", () => {
        expect(clamp_volume_percent(-1)).toBe(0)
        expect(clamp_volume_percent(101)).toBe(100)
        expect(clamp_volume_percent(150)).toBe(100)
        expect(clamp_volume_ratio(-1)).toBe(0)
        expect(clamp_volume_ratio(150)).toBe(1)
    })

    it("rounds floats and coerces numeric strings", () => {
        expect(clamp_volume_percent(33.6)).toBe(34)
        expect(clamp_volume_percent(33.4)).toBe(33)
        expect(clamp_volume_percent("50")).toBe(50)
        expect(clamp_volume_ratio("50")).toBe(0.5)
        expect(clamp_volume_ratio(33.6)).toBeCloseTo(0.34)
    })

    it("falls back to 100 percent on non-numeric input", () => {
        expect(clamp_volume_percent(Number.NaN)).toBe(100)
        expect(clamp_volume_percent(undefined)).toBe(100)
        expect(clamp_volume_percent(null)).toBe(0)
        expect(clamp_volume_percent("loud")).toBe(100)
        expect(clamp_volume_ratio(Number.NaN)).toBe(1)
        expect(clamp_volume_ratio(undefined)).toBe(1)
    })
})
