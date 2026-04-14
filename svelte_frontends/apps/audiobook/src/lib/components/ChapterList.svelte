<script lang="ts">
import { Spinner } from "@repo/ui"
import type { AudiobookChapterQueryResult } from "$lib/types/audiobook"

interface Props {
    chapters: AudiobookChapterQueryResult[]
    on_queue_chapter?: (chapter_id: number) => void
    on_delete_chapter_audio?: (chapter_id: number) => void
}

let { chapters, on_queue_chapter, on_delete_chapter_audio }: Props = $props()

function handle_queue(chapter_id: number) {
    on_queue_chapter?.(chapter_id)
}

function handle_delete(chapter_id: number) {
    on_delete_chapter_audio?.(chapter_id)
}
</script>

<div class="space-y-2">
    {#each chapters as chapter}
        <div
            class="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
        >
            <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-gray-500"> {chapter.chapter_number}. </span>
                    <span class="font-medium text-gray-900 truncate"> {chapter.chapter_title} </span>
                </div>
                <p class="text-sm text-gray-500 mt-1">{chapter.sentence_count} sentences</p>
            </div>

            <div class="flex items-center gap-2 ml-4">
                {#if chapter.has_audio}
                    <audio
                        controls
                        src={chapter.minio_presigned_url}
                        preload="metadata"
                        class="h-8 max-w-xs"
                    >
                        <track kind="captions">
                    </audio>
                    <button
                        type="button"
                        class="btn btn-danger"
                        onclick={() => handle_delete(chapter.chapter_number)}
                    >
                        Delete
                    </button>
                {:else if chapter.number_in_queue !== null}
                    <div class="flex items-center gap-2">
                        <Spinner />
                        <span class="text-sm">
                            {#if chapter.number_in_queue > 0}
                                Queued ({chapter.number_in_queue})
                            {:else}
                                Queued...
                            {/if}
                        </span>
                        <button
                            type="button"
                            class="btn btn-danger"
                            onclick={() => handle_delete(chapter.chapter_number)}
                        >
                            Remove
                        </button>
                    </div>
                {:else if chapter.is_converting}
                    <div class="flex items-center gap-2">
                        <svg
                            class="w-5 h-5 text-blue-500 animate-spin"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                stroke-width="4"
                            ></circle>
                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                        <span class="text-sm text-blue-600">Generating audio...</span>
                    </div>
                {:else}
                    <button
                        type="button"
                        class="btn btn-success"
                        onclick={() => handle_queue(chapter.chapter_number)}
                    >
                        Generate audio
                    </button>
                {/if}
            </div>
        </div>
    {/each}
</div>
