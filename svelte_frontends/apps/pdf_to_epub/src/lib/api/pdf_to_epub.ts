import { api_fetch, get_api_error_status } from "@repo/api-client"

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

export interface PdfPreviewOptions {
    chapter_mode: PdfChapterMode
    page_start: number | null
    page_end: number | null
    heuristic_sensitivity: PdfHeuristicSensitivity
    min_chapter_chars: number
    max_chapters: number
    include_images: boolean
    strip_headers: boolean
    clean_hyphens: boolean
}

export interface PdfConvertOptions extends PdfPreviewOptions {
    title: string | null
    author: string | null
    language: string | null
    use_cover: boolean
    chapter_titles: (string | null)[] | null
}

function append_pdf_preview_options(form_data: FormData, options: PdfPreviewOptions): void {
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
    form_data.append("strip_headers", String(options.strip_headers))
    form_data.append("clean_hyphens", String(options.clean_hyphens))
}

function append_pdf_options(
    form_data: FormData,
    options: PdfConvertOptions,
    preview_chapter_count?: number | null,
): void {
    append_pdf_preview_options(form_data, options)
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
    // WHY JSON-array strict-length-400: backend 400s on length mismatch/non-string
    // entries; null entries map to blank (backend keeps original), omit when null
    // or stale (length differs from preview) so convert falls back to detected titles.
    if (options.chapter_titles === null || options.chapter_titles === undefined) {
        return
    }
    if (!Array.isArray(options.chapter_titles)) {
        return
    }
    if (
        preview_chapter_count !== undefined &&
        preview_chapter_count !== null &&
        options.chapter_titles.length !== preview_chapter_count
    ) {
        return
    }
    const normalized = options.chapter_titles.map((entry) => (typeof entry === "string" ? entry : ""))
    form_data.append("chapter_titles", JSON.stringify(normalized))
}

function get_pdf_detail(error: unknown): string | null {
    // LIMITATION: ApiError from api_fetch carries status only, no response body,
    // so detail is unreachable on the live ApiError path. This passthrough only
    // applies when callers pass a plain { status, detail } object directly.
    if (typeof error === "object" && error !== null && "detail" in error) {
        const detail = (error as { detail: unknown }).detail
        if (typeof detail === "string" && detail.trim()) {
            return detail.trim()
        }
    }
    return null
}

export function get_pdf_error_message(error: unknown): string {
    const status = get_api_error_status(error)
    const detail = get_pdf_detail(error)
    const suffix = detail ? `: ${detail}` : ""
    if (status === 413) {
        return `File too large: PDF exceeds the size limit${suffix}`
    }
    if (status === 415) {
        return `Not a PDF file: upload a valid .pdf file${suffix}`
    }
    if (status === 422) {
        return `PDF cannot be processed (scanned, encrypted, or no chapters)${suffix}`
    }
    if (status === 400) {
        return `Invalid PDF request: bad page range or unreadable file${suffix}`
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
    // WHY preview subset: /preview has no title/author/language/use_cover fields.
    append_pdf_preview_options(form_data, options)
    const response = await api_fetch("/api/pdf_to_epub/preview", {
        method: "POST",
        body: form_data,
    })
    return response.json() as Promise<PdfPreviewResult>
}

export async function fetch_convert(
    file: File,
    options: PdfConvertOptions,
    preview_chapter_count?: number | null,
): Promise<Blob> {
    const form_data = new FormData()
    form_data.append("file", file)
    append_pdf_options(form_data, options, preview_chapter_count)
    const response = await api_fetch("/api/pdf_to_epub/convert", {
        method: "POST",
        body: form_data,
    })
    return response.blob()
}
