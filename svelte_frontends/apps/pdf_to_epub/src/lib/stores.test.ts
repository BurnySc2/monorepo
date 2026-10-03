import { afterEach, describe, expect, it } from "vitest"
import { load_pdf_settings, PdfSettingsSchema, reset_pdf_settings, save_pdf_settings } from "./stores"

describe("pdf settings defaults", () => {
    afterEach(() => {
        reset_pdf_settings()
    })
    it("uses auto chapter mode by default", () => {
        expect(load_pdf_settings().chapter_mode).toBe("auto")
    })

    it("uses medium sensitivity by default", () => {
        expect(load_pdf_settings().heuristic_sensitivity).toBe("medium")
    })

    it("leaves page range null by default", () => {
        expect(load_pdf_settings().page_start).toBeNull()
        expect(load_pdf_settings().page_end).toBeNull()
    })

    it("uses 500 min chars and 300 max chapters", () => {
        expect(load_pdf_settings().min_chapter_chars).toBe(500)
        expect(load_pdf_settings().max_chapters).toBe(300)
    })

    it("enables images strip clean cover by default", () => {
        const settings = load_pdf_settings()
        expect(settings.include_images).toBe(true)
        expect(settings.strip_headers).toBe(true)
        expect(settings.clean_hyphens).toBe(true)
        expect(settings.use_cover).toBe(true)
    })

    it("leaves language null by default", () => {
        expect(load_pdf_settings().language).toBeNull()
    })

    it("save then load round-trips custom values", () => {
        save_pdf_settings({
            ...load_pdf_settings(),
            chapter_mode: "single",
            page_start: 3,
            include_images: false,
            language: "de",
        })
        const loaded = load_pdf_settings()
        expect(loaded.chapter_mode).toBe("single")
        expect(loaded.page_start).toBe(3)
        expect(loaded.include_images).toBe(false)
        expect(loaded.language).toBe("de")
    })

    it("reset restores defaults after custom save", () => {
        save_pdf_settings({
            ...load_pdf_settings(),
            chapter_mode: "single",
            page_start: 3,
            include_images: false,
            language: "de",
        })
        reset_pdf_settings()
        const loaded = load_pdf_settings()
        expect(loaded.chapter_mode).toBe("auto")
        expect(loaded.page_start).toBeNull()
        expect(loaded.include_images).toBe(true)
        expect(loaded.language).toBeNull()
    })

    it.each([
        ["chapter_mode", "bogus"],
        ["heuristic_sensitivity", "ultra"],
        ["page_start", "2"],
        ["min_chapter_chars", "500"],
    ])("rejects invalid %s", (key, value) => {
        expect(() => PdfSettingsSchema.parse({ ...load_pdf_settings(), [key]: value })).toThrow()
    })
})
