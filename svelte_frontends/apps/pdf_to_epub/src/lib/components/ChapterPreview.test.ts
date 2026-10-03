import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const current_dir = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(join(current_dir, "ChapterPreview.svelte"), "utf-8")

describe("ChapterPreview render (static)", () => {
    it("accepts preview and is_loading props", () => {
        expect(source).toContain("preview")
        expect(source).toContain("is_loading")
    })

    it("shows Spinner while loading", () => {
        expect(source).toContain("Spinner")
        expect(source).toContain("is_loading")
        expect(source).toContain("Loading preview")
    })

    it("renders chapter_source badge", () => {
        expect(source).toContain("chapter_source")
        expect(source).toContain("Chapter source")
    })

    it("renders expandable outline list", () => {
        expect(source).toContain("outline")
        expect(source).toMatch(/details|<ul/)
        expect(source).toContain("Outline")
    })

    it("renders chapters grid with title chars preview", () => {
        expect(source).toContain("chapter.title")
        expect(source).toContain("chapter.chars")
        expect(source).toContain("chapter.preview")
        expect(source).toContain("grid-cols-")
        expect(source).toContain("Chapter previews")
        expect(source).not.toContain("<table")
    })

    it("renders editable title inputs bound to edited_titles with detected placeholder", () => {
        expect(source).toContain("edited_titles")
        expect(source).toContain("<input")
        expect(source).toContain("placeholder")
        expect(source).toContain("on_title_change")
    })

    it("supports per-row and all revert actions", () => {
        expect(source).toContain("on_revert_one")
        expect(source).toContain("on_revert_all")
        expect(source).toContain("Revert")
    })

    it("shows dirty badge when titles edited", () => {
        expect(source).toContain("is_dirty")
        expect(source).toContain("Edited")
    })

    it("renders warnings panel", () => {
        expect(source).toContain("warnings")
        expect(source).toContain("Warnings")
        expect(source).toContain('role="alert"')
    })
})
