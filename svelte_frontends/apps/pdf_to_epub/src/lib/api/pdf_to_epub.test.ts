import { ApiError } from "@repo/api-client"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import type { PdfConvertOptions } from "./pdf_to_epub"
import { fetch_convert, fetch_preview, fetch_probe, get_pdf_error_message } from "./pdf_to_epub"

const original_fetch = globalThis.fetch
const mock_fetch = vi.fn()

function mock_json(payload: unknown) {
    mock_fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => payload,
    })
}

function mock_blob() {
    mock_fetch.mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(["PK"], { type: "application/epub+zip" }),
    })
}

function mock_fail(status: number, statusText: string) {
    mock_fetch.mockResolvedValueOnce({
        ok: false,
        status,
        statusText,
    })
}

function base_options(overrides: Partial<PdfConvertOptions> = {}): PdfConvertOptions {
    return {
        chapter_mode: "auto",
        page_start: null,
        page_end: null,
        heuristic_sensitivity: "medium",
        min_chapter_chars: 500,
        max_chapters: 300,
        include_images: true,
        strip_headers: true,
        clean_hyphens: true,
        title: null,
        author: null,
        language: null,
        use_cover: true,
        chapter_titles: null,
        ...overrides,
    }
}

function test_file(): File {
    return new File(["%PDF-1.4 test"], "test.pdf", { type: "application/pdf" })
}

function last_form(): FormData {
    const calls = mock_fetch.mock.calls
    const init = calls[calls.length - 1][1] as { body: FormData }
    return init.body as FormData
}

describe("pdf_to_epub API", () => {
    beforeEach(() => {
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.clearAllMocks()
        vi.unstubAllEnvs()
    })

    it("fetch_probe posts file to /api/pdf_to_epub/probe", async () => {
        mock_json({ total_pages: 10, has_outline: true, has_images: false, metadata: {} })
        const result = await fetch_probe(test_file())
        expect(result.total_pages).toBe(10)
        expect(mock_fetch).toHaveBeenCalledTimes(1)
        const url = mock_fetch.mock.calls[0][0] as string
        expect(url).toContain("/api/pdf_to_epub/probe")
        const init = mock_fetch.mock.calls[0][1] as RequestInit
        expect(init.method).toBe("POST")
        const form = last_form()
        expect(form.get("file")).toBeInstanceOf(File)
    })

    it("fetch_preview posts preview keys to /api/pdf_to_epub/preview without convert-only fields", async () => {
        mock_json({ chapter_source: "single", outline: [], chapters: [], warnings: [] })
        await fetch_preview(test_file(), base_options({ title: "T", author: "A", language: "en" }))
        const url = mock_fetch.mock.calls[0][0] as string
        expect(url).toContain("/api/pdf_to_epub/preview")
        const form = last_form()
        expect(form.get("chapter_mode")).toBe("auto")
        expect(form.get("heuristic_sensitivity")).toBe("medium")
        expect(form.get("min_chapter_chars")).toBe("500")
        expect(form.get("max_chapters")).toBe("300")
        expect(form.get("include_images")).toBe("true")
        expect(form.get("strip_headers")).toBe("true")
        expect(form.get("clean_hyphens")).toBe("true")
        expect(form.has("title")).toBe(false)
        expect(form.has("author")).toBe(false)
        expect(form.has("language")).toBe(false)
        expect(form.has("use_cover")).toBe(false)
    })

    it("fetch_preview omits null page range and includes set range", async () => {
        mock_json({ chapter_source: "single", outline: [], chapters: [], warnings: [] })
        await fetch_preview(test_file(), base_options())
        expect(last_form().has("page_start")).toBe(false)
        expect(last_form().has("page_end")).toBe(false)
        mock_json({ chapter_source: "single", outline: [], chapters: [], warnings: [] })
        await fetch_preview(test_file(), base_options({ page_start: 2, page_end: 5 }))
        const form = last_form()
        expect(form.get("page_start")).toBe("2")
        expect(form.get("page_end")).toBe("5")
    })

    it("fetch_convert posts convert-only fields to /api/pdf_to_epub/convert", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ title: "T", author: "A", language: "en", use_cover: false }))
        const url = mock_fetch.mock.calls[0][0] as string
        expect(url).toContain("/api/pdf_to_epub/convert")
        const form = last_form()
        expect(form.get("title")).toBe("T")
        expect(form.get("author")).toBe("A")
        expect(form.get("language")).toBe("en")
        expect(form.get("use_cover")).toBe("false")
    })

    it("fetch_convert omits null title/author/language", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options())
        const form = last_form()
        expect(form.has("title")).toBe(false)
        expect(form.has("author")).toBe(false)
        expect(form.has("language")).toBe(false)
    })

    it("fetch_convert sends chapter_titles JSON when non-null", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: ["Intro", "Outro"] }), 2)
        const form = last_form()
        expect(form.has("chapter_titles")).toBe(true)
        expect(form.get("chapter_titles")).toBe(JSON.stringify(["Intro", "Outro"]))
    })

    it("fetch_convert omits chapter_titles when null", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: null }))
        expect(last_form().has("chapter_titles")).toBe(false)
    })

    it("fetch_convert omits chapter_titles on length mismatch (stale preview)", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: ["Only One"] }), 2)
        expect(last_form().has("chapter_titles")).toBe(false)
    })

    it("fetch_convert normalizes null entries to blank (backend keeps original)", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: [null, "Beta"] }), 2)
        expect(last_form().get("chapter_titles")).toBe(JSON.stringify(["", "Beta"]))
    })

    it("fetch_preview never sends chapter_titles (preview subset clean)", async () => {
        mock_json({ chapter_source: "single", outline: [], chapters: [], warnings: [] })
        await fetch_preview(test_file(), base_options({ chapter_titles: ["Intro", "Outro"] }))
        expect(last_form().has("chapter_titles")).toBe(false)
    })

    it("fetch_probe throws on 413/415/422/400", async () => {
        mock_fail(413, "Too Large")
        await expect(fetch_probe(test_file())).rejects.toThrow(/Request failed \/api\/pdf_to_epub\/probe/)
        mock_fail(415, "Unsupported Media Type")
        await expect(fetch_probe(test_file())).rejects.toThrow(/Request failed/)
        mock_fail(422, "Unprocessable Entity")
        await expect(fetch_probe(test_file())).rejects.toThrow(/Request failed/)
        mock_fail(400, "Bad Request")
        await expect(fetch_probe(test_file())).rejects.toThrow(/Request failed/)
    })

    it("get_pdf_error_message maps 413 file too large", () => {
        const message = get_pdf_error_message({ status: 413 })
        expect(message.toLowerCase()).toContain("file too large")
    })

    it("get_pdf_error_message maps 415 not PDF", () => {
        const message = get_pdf_error_message({ status: 415 })
        expect(message.toLowerCase()).toContain("not a pdf")
    })

    it("get_pdf_error_message maps 422 processing failure", () => {
        const message = get_pdf_error_message({ status: 422 })
        expect(message.toLowerCase()).toMatch(/scanned|encrypted|no chapters/)
    })

    it("get_pdf_error_message passes backend detail through", () => {
        const message = get_pdf_error_message({ status: 422, detail: "scanned pdf, no text layer" })
        expect(message).toContain("scanned pdf, no text layer")
    })

    it("get_pdf_error_message maps 400 bad range", () => {
        const message = get_pdf_error_message({ status: 400 })
        expect(message.toLowerCase()).toMatch(/bad|range|invalid|unreadable/)
    })

    it("get_pdf_error_message maps 409 to generic", () => {
        const message = get_pdf_error_message({ status: 409 })
        expect(message).toBe("Unknown PDF error")
    })

    it("get_pdf_error_message handles ApiError instances", () => {
        const error = new ApiError("/api/pdf_to_epub/preview", 413, "Too Large")
        expect(get_pdf_error_message(error).toLowerCase()).toContain("file too large")
        const not_pdf = new ApiError("/api/pdf_to_epub/probe", 415, "Unsupported Media Type")
        expect(get_pdf_error_message(not_pdf).toLowerCase()).toContain("not a pdf")
    })

    it("get_pdf_error_message falls back to Error message or unknown", () => {
        expect(get_pdf_error_message(new Error("boom"))).toBe("boom")
        expect(get_pdf_error_message(null)).toBe("Unknown PDF error")
    })

    it("fetch_convert sends chapter_titles when preview count omitted", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: ["Alpha", "Beta"] }), undefined)
        const form = last_form()
        expect(form.has("chapter_titles")).toBe(true)
        expect(form.get("chapter_titles")).toBe(JSON.stringify(["Alpha", "Beta"]))
    })

    it.each([
        [
            [null, "Beta"],
            ["", "Beta"],
        ],
        [
            [undefined, "Beta"],
            ["", "Beta"],
        ],
        [
            [123, "Beta"],
            ["", "Beta"],
        ],
        [
            ["", "Beta"],
            ["", "Beta"],
        ],
    ])("fetch_convert normalizes %o to %o", async (raw, want) => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: raw as unknown as (string | null)[] }), 2)
        expect(last_form().get("chapter_titles")).toBe(JSON.stringify(want))
    })

    it("fetch_convert omits chapter_titles when non-array", async () => {
        mock_blob()
        await fetch_convert(test_file(), base_options({ chapter_titles: "nope" as unknown as (string | null)[] }), 1)
        expect(last_form().has("chapter_titles")).toBe(false)
    })

    it.each([[413], [415], [422], [400]])("fetch_preview throws on %i", async (status) => {
        mock_fail(status, "fail")
        await expect(fetch_preview(test_file(), base_options())).rejects.toThrow(
            /Request failed \/api\/pdf_to_epub\/preview/,
        )
    })

    it.each([[413], [415], [422], [400]])("fetch_convert throws on %i", async (status) => {
        mock_fail(status, "fail")
        await expect(fetch_convert(test_file(), base_options())).rejects.toThrow(
            /Request failed \/api\/pdf_to_epub\/convert/,
        )
    })

    it.each([
        [413, "quota exceeded", "File too large"],
        [415, "bad magic", "Not a PDF"],
        [400, "bad range", "Invalid PDF request"],
    ])("get_pdf_error_message appends detail for %i", (status, detail, fragment) => {
        const message = get_pdf_error_message({ status, detail })
        expect(message).toContain(detail)
        expect(message).toContain(`: ${detail}`)
        expect(message.toLowerCase()).toContain(fragment.toLowerCase())
    })

    it.each([
        [{ status: 413, detail: "   " }, "File too large: PDF exceeds the size limit"],
        [{ status: 413, detail: 123 }, "File too large: PDF exceeds the size limit"],
        [{ status: 413 }, "File too large: PDF exceeds the size limit"],
        [{ status: 415, detail: "   " }, "Not a PDF file: upload a valid .pdf file"],
        [{ status: 415, detail: 123 }, "Not a PDF file: upload a valid .pdf file"],
        [{ status: 415 }, "Not a PDF file: upload a valid .pdf file"],
        [{ status: 400, detail: "   " }, "Invalid PDF request: bad page range or unreadable file"],
        [{ status: 400, detail: 123 }, "Invalid PDF request: bad page range or unreadable file"],
        [{ status: 400 }, "Invalid PDF request: bad page range or unreadable file"],
    ])("get_pdf_error_message omits blank detail %o", (input, want) => {
        expect(get_pdf_error_message(input)).toBe(want)
    })

    it("fetch_preview serializes false booleans as string false", async () => {
        mock_json({ chapter_source: "single", outline: [], chapters: [], warnings: [] })
        await fetch_preview(
            test_file(),
            base_options({ include_images: false, strip_headers: false, clean_hyphens: false }),
        )
        const form = last_form()
        expect(form.get("include_images")).toBe("false")
        expect(form.get("strip_headers")).toBe("false")
        expect(form.get("clean_hyphens")).toBe("false")
    })

    it("fetch_convert serializes false booleans as string false", async () => {
        mock_blob()
        await fetch_convert(
            test_file(),
            base_options({
                include_images: false,
                strip_headers: false,
                clean_hyphens: false,
                use_cover: false,
            }),
        )
        const form = last_form()
        expect(form.get("include_images")).toBe("false")
        expect(form.get("strip_headers")).toBe("false")
        expect(form.get("clean_hyphens")).toBe("false")
        expect(form.get("use_cover")).toBe("false")
    })

    it("fetch_probe sends file only without option keys", async () => {
        mock_json({ total_pages: 5, has_outline: false, has_images: false, metadata: {} })
        await fetch_probe(test_file())
        const form = last_form()
        expect(form.get("file")).toBeInstanceOf(File)
        expect(form.has("chapter_mode")).toBe(false)
        expect(form.has("min_chapter_chars")).toBe(false)
        expect(form.has("include_images")).toBe(false)
    })
})
