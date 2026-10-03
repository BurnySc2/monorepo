<script lang="ts">
import { Spinner } from "@repo/ui"
import type { PdfPreviewResult } from "$lib/api/pdf_to_epub"

interface Props {
    preview: PdfPreviewResult | null
    is_loading?: boolean
    edited_titles?: (string | null)[] | null
    is_dirty?: boolean
    on_title_change?: (index: number, value: string) => void
    on_revert_one?: (index: number) => void
    on_revert_all?: () => void
}

let {
    preview = null,
    is_loading = false,
    edited_titles = null,
    is_dirty = false,
    on_title_change = () => {},
    on_revert_one = () => {},
    on_revert_all = () => {},
}: Props = $props()

function title_value(index: number, fallback: string): string {
    const edited = edited_titles?.[index]
    return typeof edited === "string" ? edited : edited_titles ? (fallback ?? "") : fallback
}

function is_row_dirty(index: number, detected: string): boolean {
    if (!edited_titles || index >= edited_titles.length) {
        return false
    }
    const edited = edited_titles[index]
    return edited !== null && edited !== undefined && edited !== detected
}
</script>

<div>
    {#if is_loading}
        <div class="flex items-center gap-2">
            <Spinner />
            <p class="text-sm text-gray-600">Loading preview…</p>
        </div>
    {:else if preview}
        <p class="text-sm text-gray-600">
            <span class="inline-block rounded bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-800">
                Chapter source: {preview.chapter_source}
            </span>
            {#if is_dirty}
                <span class="ml-2 inline-block rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                    Edited
                </span>
            {/if}
        </p>
        {#if is_dirty}
            <div class="mt-2">
                <button
                    type="button"
                    onclick={on_revert_all}
                    class="rounded border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-700"
                >
                    Revert all
                </button>
            </div>
        {/if}
        <details class="mt-4">
            <summary class="cursor-pointer text-sm font-semibold">Outline ({preview.outline.length})</summary>
            {#if preview.outline.length === 0}
                <p class="text-sm text-gray-500">No outline entries.</p>
            {:else}
                <ul class="mt-2 list-disc pl-5 text-sm">
                    {#each preview.outline as entry, i (i)}
                        <li>{entry}</li>
                    {/each}
                </ul>
            {/if}
        </details>
        <div class="mt-4 text-sm">
            <h3 class="sr-only">Chapter previews</h3>
            <div
                class="hidden border-b font-semibold sm:grid sm:grid-cols-[minmax(0,2fr)_auto_minmax(0,3fr)_auto] sm:gap-2"
            >
                <div class="text-left">Title</div>
                <div class="text-left sm:whitespace-nowrap">Chars</div>
                <div class="text-left">Preview</div>
                <div class="text-left sm:whitespace-nowrap"><span class="sr-only">Actions</span></div>
            </div>
            <div class="flex flex-col gap-3 sm:gap-0">
                {#if preview.chapters.length === 0}
                    <div class="py-1 text-gray-500">No chapters found for this preview.</div>
                {:else}
                    {#each preview.chapters as chapter, i (i)}
                        <div
                            class="grid grid-cols-1 gap-1 border-b py-2 sm:grid-cols-[minmax(0,2fr)_auto_minmax(0,3fr)_auto] sm:gap-2 sm:py-1"
                        >
                            <!-- WHY input per row: in-place rename keeps detected order. -->
                            <div class="min-w-0 sm:pr-2">
                                <span class="text-xs font-semibold text-gray-500 sm:hidden">Title</span>
                                <input
                                    type="text"
                                    value={title_value(i, chapter.title)}
                                    placeholder={chapter.title}
                                    aria-label={`Chapter ${i + 1} title`}
                                    maxlength={200}
                                    oninput={(e) => on_title_change(i, e.currentTarget.value)}
                                    class="w-full min-w-0 rounded border px-2 py-1"
                                >
                            </div>
                            <div class="min-w-0 sm:pr-2 sm:whitespace-nowrap">
                                <span class="text-gray-500 sm:hidden">Chars: </span>{chapter.chars}
                            </div>
                            <div class="min-w-0 break-words text-gray-600">
                                <span class="text-xs font-semibold text-gray-500 sm:hidden">Preview: </span>
                                {chapter.preview}
                            </div>
                            <div class="min-w-0 sm:whitespace-nowrap">
                                <button
                                    type="button"
                                    onclick={() => on_revert_one(i)}
                                    disabled={!is_row_dirty(i, chapter.title)}
                                    aria-label={`Revert chapter ${i + 1} title`}
                                    class="rounded border border-gray-300 px-2 py-1 text-xs disabled:opacity-50"
                                >
                                    Revert
                                </button>
                            </div>
                        </div>
                    {/each}
                {/if}
            </div>
        </div>
        {#if preview.warnings.length > 0}
            <div
                role="alert"
                class="mt-4 rounded border border-amber-200 bg-amber-50 p-3"
            >
                <h4 class="text-sm font-semibold text-amber-800">Warnings</h4>
                <ul class="mt-1 list-disc pl-5 text-sm text-amber-700">
                    {#each preview.warnings as warning, i (i)}
                        <li>{warning}</li>
                    {/each}
                </ul>
            </div>
        {/if}
    {:else}
        <p class="text-sm text-gray-500">No preview yet. Upload a PDF and choose Preview.</p>
    {/if}
</div>
