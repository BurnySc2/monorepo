<script lang="ts">
import BookUpload from "$lib/components/BookUpload.svelte"
import ChapterPreview from "$lib/components/ChapterPreview.svelte"
import type { PdfSettings } from "$lib/stores"
import { is_loading, load_pdf_settings, save_pdf_settings } from "$lib/stores"

let selected_file: File | null = $state(null)
let parser: PdfSettings["parser"] = $state(load_pdf_settings().parser)
let chapter_mode: PdfSettings["chapter_mode"] = $state(load_pdf_settings().chapter_mode)
let heuristic_sensitivity: PdfSettings["heuristic_sensitivity"] = $state(load_pdf_settings().heuristic_sensitivity)
let page_start: number | null = $state(load_pdf_settings().page_start)
let page_end: number | null = $state(load_pdf_settings().page_end)
let min_chapter_chars: number = $state(load_pdf_settings().min_chapter_chars)
let max_chapters: number = $state(load_pdf_settings().max_chapters)
let include_images: boolean = $state(load_pdf_settings().include_images)
let include_tables: boolean = $state(load_pdf_settings().include_tables)
let strip_headers: boolean = $state(load_pdf_settings().strip_headers)
let clean_hyphens: boolean = $state(load_pdf_settings().clean_hyphens)
let use_cover: boolean = $state(load_pdf_settings().use_cover)
let language: string | null = $state(load_pdf_settings().language)
let book_title: string = $state("")
let book_author: string = $state("")
let step: "upload" | "options" | "preview" = $state("upload")

async function handle_upload(file: File) {
    selected_file = file
    step = "options"
    // TODO: wire upload to fetch_probe (/api/pdf_to_epub/probe), prefill title/author/language from probe.metadata
}

function handle_options_submit() {
    save_pdf_settings({
        parser,
        chapter_mode,
        heuristic_sensitivity,
        page_start,
        page_end,
        min_chapter_chars,
        max_chapters,
        include_images,
        include_tables,
        strip_headers,
        clean_hyphens,
        use_cover,
        language,
    })
    step = "preview"
    // TODO: wire Preview button to fetch_preview, render ChapterPreview + warnings panel + Spinner
    // TODO: wire Convert and Download button to fetch_convert blob download
}
</script>

<div class="container mx-auto max-w-4xl px-4 py-8">
    <h1 class="text-3xl font-bold text-center mb-4">PDF to EPUB</h1>
    <p class="text-sm text-gray-500 text-center mb-6">Upload &rarr; Options &rarr; Preview &rarr; Download</p>

    {#if is_loading.value}
        <p class="text-sm text-gray-500 text-center">Loading settings…</p>
    {/if}

    {#if step === "upload"}
        <section aria-label="Upload">
            <h2 class="text-xl font-semibold mb-3">1. Upload PDF</h2>
            <BookUpload on_upload={handle_upload} />
            <!-- TODO: wire upload to fetch_probe per SPEC.md section 8 -->
        </section>
    {/if}

    {#if step === "options" || step === "preview"}
        <section
            aria-label="Options"
            class="mt-8"
        >
            <h2 class="text-xl font-semibold mb-3">2. Conversion options</h2>
            <form
                onsubmit={(e) => {
                    e.preventDefault()
                    handle_options_submit()
                }}
                class="grid gap-4"
            >
                <label class="grid gap-1">
                    <span>Parser</span>
                    <select
                        bind:value={parser}
                        class="border rounded px-2 py-1"
                    >
                        <option value="balanced">balanced</option>
                        <option value="minimal">minimal</option>
                        <option value="max_quality">max_quality</option>
                    </select>
                    <!-- TODO: license badge for max_quality (AGPL pymupdf, lazy import, opt-in) per SPEC.md -->
                </label>
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
                    <!-- TODO: parse chapter_mode auto/outline/heuristic/single per SPEC.md -->
                </label>
                <!-- TODO: heuristic_sensitivity slider low/medium/high per SPEC.md -->
                <div class="flex gap-4">
                    <label class="grid gap-1">
                        <span>Page start</span>
                        <input
                            type="number"
                            bind:value={page_start}
                            placeholder="First page"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                    <label class="grid gap-1">
                        <span>Page end</span>
                        <input
                            type="number"
                            bind:value={page_end}
                            placeholder="Last page"
                            class="border rounded px-2 py-1"
                        >
                    </label>
                    <!-- TODO: parse page range per SPEC.md -->
                </div>
                <!-- TODO: number inputs for min_chapter_chars (default 500) and max_chapters (default 300) per SPEC.md -->
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={include_images}
                    >
                    <span>Include images</span>
                    <!-- TODO: parse include_images/tables per SPEC.md -->
                </label>
                <label class="flex items-center gap-2">
                    <input
                        type="checkbox"
                        bind:checked={include_tables}
                    >
                    <span>Include tables</span>
                </label>
                <!-- TODO: checkboxes for strip_headers, clean_hyphens, use_cover per SPEC.md -->
                <label class="grid gap-1">
                    <span>Title (metadata edit)</span>
                    <input
                        type="text"
                        bind:value={book_title}
                        placeholder="Book title"
                        class="border rounded px-2 py-1"
                    >
                    <!-- TODO: prefill title/author/language from probe.metadata, editable per SPEC.md -->
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
                <!-- TODO: text input for language prefilled from probe.metadata per SPEC.md -->
                <button
                    type="submit"
                    class="btn btn-primary px-4 py-2 rounded bg-blue-600 text-white"
                >
                    Continue to preview
                </button>
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
            <ChapterPreview preview={null} />
            <!-- TODO: wire fetch_preview result + warnings panel + Spinner per SPEC.md -->
        </section>

        <section
            aria-label="Download"
            class="mt-8"
        >
            <h2 class="text-xl font-semibold mb-3">4. Download</h2>
            <p class="text-sm text-gray-500">Download button placeholder.</p>
            <!-- TODO: wire fetch_convert blob download per SPEC.md -->
        </section>
    {/if}
</div>
