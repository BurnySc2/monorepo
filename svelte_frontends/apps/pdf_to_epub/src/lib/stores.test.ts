import { describe, expect, it } from "vitest"
import { load_pdf_settings } from "./stores"

describe("pdf settings defaults", () => {
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
})
