// API stubs for PDF to EPUB feature.
// TODO: implement probe/preview/convert calls per SPEC.md root.
// Endpoints use snake_case prefix /api/pdf_to_epub per SPEC.md section 8.

import { api_fetch, get_api_error_status } from "@repo/api-client"

// UI parser vocabulary per SPEC.md table + section 9.
// balanced = pypdf + pdfplumber (Option A, default).
// minimal = pypdf only (Option B).
// max_quality = balanced + pymupdf (Option C, AGPL, lazy import, opt-in only).
// TODO: show license badge for max_quality in options UI.
export type PdfParser = "balanced" | "minimal" | "max_quality"
export type PdfChapterMode = "auto" | "outline" | "heuristic" | "single"
export type PdfHeuristicSensitivity = "low" | "medium" | "high"
export type PdfChapterSource = "outline" | "heuristic" | "single"

export interface PdfProbeMetadata {
    title: string | null
    author: string | null
    language: string | null
}

export interface PdfProbeResult {
    total_pages: number
    has_outline: boolean
    has_images: boolean
    metadata: PdfProbeMetadata
}

export interface PdfPreviewChapter {
    title: string
    chars: number
    preview: string
}

export interface PdfPreviewResult {
    chapter_source: PdfChapterSource
    outline: string[]
    chapters: PdfPreviewChapter[]
    warnings: string[]
}

export interface PdfConvertOptions {
    parser: PdfParser
    chapter_mode: PdfChapterMode
    page_start: number | null
    page_end: number | null
    heuristic_sensitivity: PdfHeuristicSensitivity
    min_chapter_chars: number
    max_chapters: number
    include_images: boolean
    include_tables: boolean
    strip_headers: boolean
    clean_hyphens: boolean
    title: string | null
    author: string | null
    language: string | null
    use_cover: boolean
}

function append_pdf_options(form_data: FormData, options: PdfConvertOptions): void {
    form_data.append("parser", options.parser)
    form_data.append("chapter_mode", options.chapter_mode)
    if (options.page_start !== null) {
        form_data.append("page_start", String(options.page_start))
    }
    if (options.page_end !== null) {
        form_data.append("page_end", String(options.page_end))
    }
    form_data.append("heuristic_sensitivity", options.heuristic_sensitivity)
    form_data.append("min_chapter_chars", String(options.min_chapter_chars))
    form_data.append("max_chapters", String(options.max_chapters))
    form_data.append("include_images", String(options.include_images))
    form_data.append("include_tables", String(options.include_tables))
    form_data.append("strip_headers", String(options.strip_headers))
    form_data.append("clean_hyphens", String(options.clean_hyphens))
    if (options.title !== null) {
        form_data.append("title", options.title)
    }
    if (options.author !== null) {
        form_data.append("author", options.author)
    }
    if (options.language !== null) {
        form_data.append("language", options.language)
    }
    form_data.append("use_cover", String(options.use_cover))
}

// TODO: map backend statuses to friendly messages once backend exists.
export function get_pdf_error_message(error: unknown): string {
    const status = get_api_error_status(error)
    if (status === 413) {
        return "TODO: file too large (413)"
    }
    if (status === 415) {
        return "TODO: not a PDF (415)"
    }
    if (status === 422) {
        return "TODO: scanned/encrypted/no chapters (422)"
    }
    if (status === 409) {
        return "TODO: already uploaded (409)"
    }
    return error instanceof Error ? error.message : "Unknown PDF error"
}

export async function fetch_probe(file: File): Promise<PdfProbeResult> {
    const form_data = new FormData()
    form_data.append("file", file)
    const response = await api_fetch("/api/pdf_to_epub/probe", {
        method: "POST",
        body: form_data,
    })
    return response.json() as Promise<PdfProbeResult>
}

export async function fetch_preview(file: File, options: PdfConvertOptions): Promise<PdfPreviewResult> {
    const form_data = new FormData()
    form_data.append("file", file)
    append_pdf_options(form_data, options)
    const response = await api_fetch("/api/pdf_to_epub/preview", {
        method: "POST",
        body: form_data,
    })
    return response.json() as Promise<PdfPreviewResult>
}

export async function fetch_convert(file: File, options: PdfConvertOptions): Promise<Blob> {
    const form_data = new FormData()
    form_data.append("file", file)
    append_pdf_options(form_data, options)
    const response = await api_fetch("/api/pdf_to_epub/convert", {
        method: "POST",
        body: form_data,
    })
    return response.blob()
}
