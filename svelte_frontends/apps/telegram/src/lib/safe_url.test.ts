import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import { is_safe_http_url } from "./format"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

describe("is_safe_http_url", () => {
    it.each([
        ["https://example.com"],
        ["https://t.me/c/123/456"],
        ["http://example.com/file"],
    ])("returns true for safe http url %s (renders link)", (url) => {
        expect(is_safe_http_url(url)).toBe(true)
    })

    it.each([
        ["javascript:alert(1)"],
        ["JaVaScRiPt:alert(1)"],
        ["data:text/html,<script>alert(1)</script>"],
        ["vbscript:msgbox(1)"],
        ["ftp://example.com/file"],
        ["//example.com/file"],
        [""],
    ])("returns false for unsafe url %s (renders span)", (url) => {
        expect(is_safe_http_url(url)).toBe(false)
    })

    it.each([[null], [undefined], [123], [{}], [[]], [true]])("returns false for non-string %s", (url) => {
        expect(is_safe_http_url(url)).toBe(false)
    })

    it("is case-sensitive safe: only lowercase http(s) scheme passes", () => {
        expect(is_safe_http_url("HTTPS://example.com")).toBe(false)
        expect(is_safe_http_url("HTTP://example.com")).toBe(false)
    })
})

describe("is_safe_http_url properties", () => {
    it("never throws and only http(s) strings pass", () => {
        fc.assert(
            fc.property(fc.anything(), (value) => {
                const result = is_safe_http_url(value)
                expect(typeof result).toBe("boolean")
                if (result) {
                    expect(typeof value).toBe("string")
                    expect(/^https?:\/\//.test(value as string)).toBe(true)
                }
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
