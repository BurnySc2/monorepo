<script lang="ts">
import { Spinner, toast } from "@repo/ui"
import type { PdfConvertOptions, PdfPreviewResult, PdfProbeResult } from "$lib/api/pdf_to_epub"
import { fetch_convert, fetch_preview, fetch_probe, get_pdf_error_message } from "$lib/api/pdf_to_epub"
import BookUpload from "$lib/components/BookUpload.svelte"
import ChapterPreview from "$lib/components/ChapterPreview.svelte"
import type { PdfSettings } from "$lib/stores"
import { load_pdf_settings, save_pdf_settings } from "$lib/stores"

let selected_file: File | null = $state(null)
let chapter_mode: PdfSettings["chapter_mode"] = $state(load_pdf_settings().chapter_mode)
let heuristic_sensitivity: PdfSettings["heuristic_sensitivity"] = $state(load_pdf_settings().heuristic_sensitivity)
let page_start: number | null = $state(load_pdf_settings().page_start)
let page_end: number | null = $state(load_pdf_settings().page_end)
let min_chapter_chars: number = $state(load_pdf_settings().min_chapter_chars)
let max_chapters: number = $state(load_pdf_settings().max_chapters)
let include_images: boolean = $state(load_pdf_settings().include_images)
let strip_headers: boolean = $state(load_pdf_settings().strip_headers)
let clean_hyphens: boolean = $state(load_pdf_settings().clean_hyphens)
let use_cover: boolean = $state(load_pdf_settings().use_cover)
let language: string | null = $state(load_pdf_settings().language)
let book_title: string = $state("")
let book_author: string = $state("")
let step: "upload" | "options" | "preview" = $state("upload")
let is_probing = $state(false)
let is_previewing = $state(false)
let is_converting = $state(false)
let probe_result: PdfProbeResult | null = $state(null)
let preview_result: PdfPreviewResult | null = $state(null)
let edited_titles: (string | null)[] | null = $state(null)
let preview_snapshot: string | null = $state(null)

let is_dirty = $derived.by(() => {
    const titles = edited_titles
    const preview = preview_result
    if (titles === null || preview === null) {
        return false
    }
    if (titles.length !== preview.chapters.length) {
        return false
    }
    return titles.some((entry, index) => entry !== preview.chapters[index].title)
})

function preview_key(): string {
    return JSON.stringify({
        chapter_mode,
        page_start: normalize_page(page_start),
        page_end: normalize_page(page_end),
        heuristic_sensitivity,
        min_chapter_chars,
        max_chapters,
        include_images,
        strip_headers,
        clean_hyphens,
    })
}

let is_stale = $derived(preview_result !== null && preview_snapshot !== null && preview_key() !== preview_snapshot)
let is_busy = $derived(is_previewing || is_converting)

function normalize_page(value: number | null): number | null {
    if (value === null || value === undefined) {
        return null
    }
    if (typeof value !== "number" || Number.isNaN(value)) {
        return null
    }
    return value
}

function build_convert_options(): PdfConvertOptions {
    const trimmed_title = book_title.trim()
    const trimmed_author = book_author.trim()
    const trimmed_language = (language ?? "").trim()
    // WHY strict-length: backend 400s when chapter_titles length differs from
    // detected chapters; omit on mismatch so convert uses detected titles.
    let chapter_titles: (string | null)[] | null = null
    if (edited_titles !== null && preview_result !== null && edited_titles.length === preview_result.chapters.length) {
        chapter_titles = edited_titles.map((entry) => (typeof entry === "string" ? entry : ""))
    }
    return {
        chapter_mode,
        page_start: normalize_page(page_start),
        page_end: normalize_page(page_end),
        heuristic_sensitivity,
        min_chapter_chars,
        max_chapters,
        include_images,
        strip_headers,
        clean_hyphens,
        title: trimmed_title ? trimmed_title : null,
        author: trimmed_author ? trimmed_author : null,
        language: trimmed_language ? trimmed_language : null,
        use_cover,
        chapter_titles,
    }
}

function persist_options(): void {
    save_pdf_settings({
        chapter_mode,
        heuristic_sensitivity,
        page_start: normalize_page(page_start),
        page_end: normalize_page(page_end),
        min_chapter_chars,
        max_chapters,
        include_images,
        strip_headers,
        clean_hyphens,
        use_cover,
        language: (language ?? "").trim() ? (language ?? "").trim() : null,
    })
}

function handle_title_change(index: number, value: string): void {
    if (!edited_titles) {
        return
    }
    edited_titles[index] = value
}

function revert_one(index: number): void {
    if (!edited_titles || !preview_result) {
        return
    }
    edited_titles[index] = preview_result.chapters[index].title
}

function revert_all(): void {
    if (!preview_result) {
        return
    }
    edited_titles = preview_result.chapters.map((chapter) => chapter.title)
}

async function handle_upload(file: File) {
    selected_file = file
    probe_result = null
    preview_result = null
    edited_titles = null
    preview_snapshot = null
    is_probing = true
    try {
        probe_result = await fetch_probe(file)
        if (probe_result.metadata.title && !book_title) {
            book_title = probe_result.metadata.title
        }
        if (probe_result.metadata.author && !book_author) {
            book_author = probe_result.metadata.author
        }
        if (probe_result.metadata.language && !language) {
            language = probe_result.metadata.language
        }
        step = "options"
    } catch (error) {
        toast.error(get_pdf_error_message(error))
    } finally {
        is_probing = false
    }
}

async function handle_preview() {
    if (!selected_file) {
        toast.error("Upload a PDF first")
        return
    }
    if (is_busy) {
        return
    }
    is_previewing = true
    try {
        persist_options()
        const options = build_convert_options()
        preview_result = await fetch_preview(selected_file, options)
        edited_titles = preview_result.chapters.map((chapter) => chapter.title)
        preview_snapshot = preview_key()
        step = "preview"
    } catch (error) {
        toast.error(get_pdf_error_message(error))
    } finally {
        is_previewing = false
    }
}

async function handle_convert() {
    if (!selected_file) {
        toast.error("Upload a PDF first")
        return
    }
    if (!preview_result) {
        toast.error("Preview first to detect chapters")
        return
    }
    if (edited_titles !== null && preview_result !== null && edited_titles.length !== preview_result.chapters.length) {
        toast.error("Preview is stale: options changed chapter count, re-preview before convert")
        return
    }
    if (is_stale) {
        toast.error("Options changed after preview: re-preview before convert")
        return
    }
    if (is_busy) {
        return
    }
    is_converting = true
    try {
        persist_options()
        const options = build_convert_options()
        const blob = await fetch_convert(selected_file, options, preview_result.chapters.length)
        const base_name = selected_file.name.replace(/\.pdf$/i, "") || "book"
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = url
        anchor.download = `${base_name}.epub`
        document.body.appendChild(anchor)
        anchor.click()
        anchor.remove()
        URL.revokeObjectURL(url)
        toast.success("EPUB downloaded")
    } catch (error) {
        toast.error(get_pdf_error_message(error))
    } finally {
        is_converting = false
    }
}

async function handle_options_submit() {
    await handle_preview()
}
</script>

<div class="container mx-auto max-w-4xl px-4 py-8">
    <h1 class="text-3xl font-bold text-center mb-4">PDF to EPUB</h1>
    <p class="text-sm text-gray-500 text-center mb-6">Upload &rarr; Options &rarr; Preview &rarr; Download</p>

    {#if step === "upload"}
        <section aria-label="Upload">
            <h2 class="text-xl font-semibold mb-3">1. Upload PDF</h2>
            <BookUpload
                on_upload={handle_upload}
                is_uploading={is_probing}
            />
        </section>
    {/if}

    {#if step === "options" || step === "preview"}
        <section
            aria-label="Options"
            class="mt-8"
        >
            <h2 class="text-xl font-semibold mb-3">2. Conversion options</h2>
            {#if probe_result}
                <div class="mb-4 rounded border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
                    <p>Total pages: {probe_result.total_pages}</p>
                    <p>Has outline: {probe_result.has_outline ? "yes" : "no"}</p>
                    <p>Has images: {probe_result.has_images ? "yes" : "no"}</p>
                </div>
            {/if}
            <form
                onsubmit={(e) => {
                    e.preventDefault()
                    handle_options_submit()
                }}
                class="grid gap-4"
            >
                <label class="grid gap-1">
                    <span>Chapter mode</span>
                    <select
                        bind:value={chapter_mode}
                        class="border rounded px-2 py-1"
                    >
                        <option value="auto">auto</option>
                        <option value="outline">outline</option>
                        <option value="heuristic">heuristic</option>
                        <option value="single">single</option>
                    </select>
                </label>
                <label class="grid gap-1">
                    <span
                        >Heuristic sensitivity
                        <span
                            title="Low: numbered headings only. Medium (default): also caps and keyword headings. High: also numeric and page-top short headings (more false positives). Only used for heuristic and auto fallback; single ignores it."
                            aria-label="Heuristic sensitivity details"
                            >ⓘ</span
                        >
                    </span>
                    <select
                        bind:value={heuristic_sensitivity}
                        class="border rounded px-2 py-1"
                    >
                        <option value="low">low</option>
                        <option value="medium">medium</option>
                        <option value="high">high</option>
                    </select>
                </label>
                <div class="flex gap-4">
                    <label class="grid gap-1">
                        <span>Page start</span>
                        <input
                            type="number"
                            min="1"
                            step="1"
                            bind:value={page_start}
                            placeholder="First page"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                    <label class="grid gap-1">
                        <span>Page end</span>
                        <input
                            type="number"
                            min="1"
                            step="1"
                            bind:value={page_end}
                            placeholder="Last page"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                </div>
                <div class="flex gap-4">
                    <label class="grid gap-1">
                        <span>Min chapter chars</span>
                        <input
                            type="number"
                            min="1"
                            step="1"
                            bind:value={min_chapter_chars}
                            placeholder="500"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                    <label class="grid gap-1">
                        <span>Max chapters</span>
                        <input
                            type="number"
                            min="1"
                            step="1"
                            bind:value={max_chapters}
                            placeholder="300"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                </div>
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={include_images}
                    >
                    <span>Include images</span>
                </label>
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={strip_headers}
                    >
                    <span>Strip headers</span>
                </label>
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={clean_hyphens}
                    >
                    <span>Clean hyphens</span>
                </label>
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={use_cover}
                    >
                    <span>Use cover</span>
                </label>
                <p class="text-xs text-gray-500">Title, author, language and cover affect Convert only, not Preview.</p>
                <label class="grid gap-1">
                    <span>Title (metadata edit)</span>
                    <input
                        type="text"
                        bind:value={book_title}
                        placeholder="Book title"
                        class="border rounded px-2 py-1"
                    >
                </label>
                <label class="grid gap-1">
                    <span>Author (metadata edit)</span>
                    <input
                        type="text"
                        bind:value={book_author}
                        placeholder="Book author"
                        class="border rounded px-2 py-1"
                    >
                </label>
                <label class="grid gap-1">
                    <span>Language</span>
                    <input
                        type="text"
                        bind:value={language}
                        placeholder="en"
                        class="border rounded px-2 py-1"
                    >
                </label>
                <div class="flex gap-2">
                    <button
                        type="submit"
                        disabled={is_busy || !selected_file}
                        class="btn btn-primary inline-flex items-center justify-center gap-2 px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
                    >
                        {#if is_previewing}
                            <Spinner />
                            <span>Previewing…</span>
                        {:else}
                            <span>Preview</span>
                        {/if}
                    </button>
                    <button
                        type="button"
                        onclick={handle_convert}
                        disabled={is_busy || !selected_file || !preview_result || is_stale}
                        title="Preview required - run Preview first"
                        class="inline-flex items-center justify-center gap-2 px-4 py-2 rounded bg-green-600 text-white disabled:opacity-50"
                    >
                        {#if is_converting}
                            <Spinner />
                            <span>Converting…</span>
                        {:else}
                            <span>Convert & Download</span>
                        {/if}
                    </button>
                </div>
            </form>
        </section>
    {/if}

    {#if step === "preview"}
        <section
            aria-label="Preview"
            class="mt-8"
        >
            <h2 class="text-xl font-semibold mb-3">3. Preview</h2>
            {#if selected_file}
                <p class="text-sm text-gray-600">Selected file: {selected_file.name}</p>
            {/if}
            {#if is_stale}
                <div
                    role="alert"
                    class="mt-2 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700"
                >
                    Options changed after preview: re-preview to refresh chapter titles before convert.
                </div>
            {/if}
            <ChapterPreview
                preview={preview_result}
                is_loading={is_previewing}
                {edited_titles}
                {is_dirty}
                on_title_change={handle_title_change}
                on_revert_one={revert_one}
                on_revert_all={revert_all}
            />
        </section>

        <section
            aria-label="Download"
            class="mt-8"
        >
            <h2 class="text-xl font-semibold mb-3">4. Download</h2>
            {#if is_stale}
                <p class="text-sm text-amber-700">Preview is stale: re-preview before convert.</p>
            {:else}
                <p class="text-sm text-gray-500">Convert uses edited chapter titles.</p>
            {/if}
            <button
                type="button"
                onclick={handle_convert}
                disabled={is_busy || !selected_file || !preview_result || is_stale}
                title="Preview required - run Preview first"
                class="mt-2 inline-flex items-center justify-center gap-2 px-4 py-2 rounded bg-green-600 text-white disabled:opacity-50"
            >
                {#if is_converting}
                    <Spinner />
                    <span>Converting…</span>
                {:else}
                    <span>Convert & Download</span>
                {/if}
            </button>
        </section>
    {/if}
</div>
