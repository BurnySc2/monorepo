<script lang="ts">
import type { ChapterDetail as AudiobookChapterQueryResult } from "@repo/api-types"
import { Spinner } from "@repo/ui"

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
                    <a
                        href={chapter.minio_presigned_url}
                        download
                        type="button"
                        class="btn btn-primary"
                    >
                        Download
                    </a>
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
                            {#if (chapter.number_in_queue ?? 0) > 0}
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
                        <Spinner />
                        <span class="text-sm">Generating audio...</span>
                    </div>
                    <button
                        type="button"
                        class="btn btn-danger"
                        onclick={() => handle_delete(chapter.chapter_number)}
                    >
                        Delete
                    </button>
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
