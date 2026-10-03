import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const current_dir = dirname(fileURLToPath(import.meta.url))
const source = readFileSync(join(current_dir, "BookUpload.svelte"), "utf-8")

describe("BookUpload PDF accept (static)", () => {
    it("accepts .pdf files in file picker", () => {
        expect(source).toContain('accept = ".pdf"')
    })

    it("validates .pdf extension on drop", () => {
        expect(source).toContain(".pdf")
        expect(source).toContain("toLowerCase()")
        expect(source).toContain("endsWith")
    })

    it("shows toast error for non-pdf files", () => {
        expect(source).toContain("toast.error")
        expect(source).toContain(".pdf")
    })

    it("exposes on_upload callback prop", () => {
        expect(source).toContain("on_upload")
    })

    it("shows Spinner while uploading", () => {
        expect(source).toContain("Spinner")
        expect(source).toContain("is_uploading")
    })

    it("supports disabled state", () => {
        expect(source).toContain("disabled")
    })
})
