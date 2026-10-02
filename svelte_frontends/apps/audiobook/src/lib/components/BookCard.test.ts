import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

// Component mount is not feasible: audiobook has no @testing-library/svelte
// and no jsdom/happy-dom (adding them would be high-risk for Gate3).
// This structural test guards the critical fix: delete button must live
// outside the <a> link so clicking delete never navigates, and IconDelete
// must render for the affordance.
const current_dir = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(join(current_dir, "BookCard.svelte"), "utf-8")

describe("BookCard delete affordance (static)", () => {
    it("renders IconDelete", () => {
        expect(source).toContain("IconDelete")
        expect(source).toContain('import { IconDelete } from "@repo/ui"')
    })

    it("places delete button outside the link", () => {
        const anchor_close = source.indexOf("</a>")
        const button_open = source.indexOf("<button", source.indexOf("{#if on_delete}"))
        expect(anchor_close).toBeGreaterThan(-1)
        expect(button_open).toBeGreaterThan(-1)
        expect(button_open).toBeGreaterThan(anchor_close)
    })

    it("delete button stops navigation", () => {
        expect(source).toContain("event.preventDefault()")
        expect(source).toContain("event.stopPropagation()")
    })

    it("exposes delete accessible label", () => {
        expect(source).toContain("Delete book")
    })
})
