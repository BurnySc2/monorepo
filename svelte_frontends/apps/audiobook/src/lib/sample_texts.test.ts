import * as fc from "fast-check"
import { describe, expect, it } from "vitest"
import { lang_subtag, pick_sample, SAMPLE_TEXT_VERSION, SAMPLE_TEXTS } from "./sample_texts"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

describe("sample_texts", () => {
    it("exposes a numeric version", () => {
        expect(typeof SAMPLE_TEXT_VERSION).toBe("number")
    })

    it("resolves the fallback chain", () => {
        const cases: Array<[locale: string, key: string, is_fallback: boolean]> = [
            ["pt-BR", "pt", true],
            ["pt_BR", "pt", true],
            ["xx", "en", true],
            ["en", "en", false],
        ]
        for (const [locale, key, is_fallback] of cases) {
            const pick = pick_sample(locale)
            expect(pick.key, locale).toBe(key)
            expect(pick.text, locale).toBe(SAMPLE_TEXTS[key])
            expect(pick.is_fallback, locale).toBe(is_fallback)
        }
    })

    it("keeps every entry non-empty and within limit", () => {
        for (const [key, text] of Object.entries(SAMPLE_TEXTS)) {
            expect(text.length, key).toBeGreaterThanOrEqual(1)
            expect(text.length, key).toBeLessThanOrEqual(1500)
        }
    })

    it("pick_sample never throws and stays within contract", () => {
        fc.assert(
            fc.property(fc.string({ maxLength: 20 }), (locale) => {
                const pick = pick_sample(locale)
                expect(pick.key in SAMPLE_TEXTS).toBe(true)
                expect(pick.text).toBe(SAMPLE_TEXTS[pick.key])
                expect(pick.text.length).toBeGreaterThanOrEqual(1)
                expect(pick.text.length).toBeLessThanOrEqual(1500)
                const full = locale.trim().toLowerCase().replace(/_/g, "-")
                if (!(full in SAMPLE_TEXTS) && !(lang_subtag(locale) in SAMPLE_TEXTS)) {
                    expect(pick.key).toBe("en")
                }
            }),
            { seed: FC_SEED, numRuns: 50 },
        )
    })

    it("lang_subtag lowercases and splits on dash or underscore", () => {
        fc.assert(
            fc.property(fc.string({ maxLength: 20 }), (locale) => {
                const sub = lang_subtag(locale)
                expect(sub).toBe(sub.toLowerCase())
                expect(sub.includes("-")).toBe(false)
                expect(sub.includes("_")).toBe(false)
                expect(locale.trim().toLowerCase().startsWith(sub)).toBe(true)
            }),
            { seed: FC_SEED, numRuns: 50 },
        )
    })
})
