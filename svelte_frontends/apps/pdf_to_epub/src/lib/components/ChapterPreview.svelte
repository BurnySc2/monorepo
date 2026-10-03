<script lang="ts">
// Placeholder for SPEC.md section 11 ChapterPreview.svelte.
// SPEC.md section 11 lists PdfUpload.svelte + ChapterPreview.svelte; this app
// currently clones BookUpload.svelte from apps/audiobook (see BookUpload.svelte).
// TODO(@documenter): reconcile SPEC section 11 file list with actual components.
// TODO: render PdfPreviewResult envelope (chapter_source badge, outline,
// chapters with title/chars/preview, warnings) plus Spinner during fetch_preview.
import type { PdfPreviewResult } from "$lib/api/pdf_to_epub"

interface Props {
    preview: PdfPreviewResult | null
}

let { preview = null }: Props = $props()
</script>

<div>
    {#if preview}
        <p class="text-sm text-gray-600">Chapter source: {preview.chapter_source}</p>
    <!-- TODO: wire expandable TOC + per-chapter char counts + preview snippet + warnings panel -->
    {:else}
        <p class="text-sm text-gray-500">Preview list placeholder.</p>
    {/if}
</div>
