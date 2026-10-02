<script lang="ts">
import type { BookListItemSchema as AudiobookBook } from "@repo/api-types"
import { format_date_string } from "@repo/sc2-utils"
import { IconClock, IconDelete, IconList } from "@repo/ui"
import { onDestroy } from "svelte"

interface Props {
    book: AudiobookBook
    on_delete?: (book_id: number) => void
}

let { book, on_delete }: Props = $props()

let confirm_armed = $state(false)
let reset_timer: ReturnType<typeof setTimeout> | null = null

function handle_delete(event: MouseEvent) {
    event.preventDefault()
    event.stopPropagation()
    if (!confirm_armed) {
        confirm_armed = true
        if (reset_timer) {
            clearTimeout(reset_timer)
        }
        reset_timer = setTimeout(() => {
            confirm_armed = false
        }, 3000)
        return
    }
    if (reset_timer) {
        clearTimeout(reset_timer)
        reset_timer = null
    }
    confirm_armed = false
    on_delete?.(book.id)
}

function handle_keydown(event: KeyboardEvent) {
    if (event.key === "Escape" && confirm_armed) {
        confirm_armed = false
        if (reset_timer) {
            clearTimeout(reset_timer)
            reset_timer = null
        }
    }
}

onDestroy(() => {
    if (reset_timer) {
        clearTimeout(reset_timer)
    }
})

const display_title = $derived(book.custom_book_title || book.book_title)
const display_author = $derived(book.custom_book_author || book.book_author)
const formatted_date = $derived(format_date_string(book.upload_date))
</script>

<div class="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200 border border-gray-200">
    <div class="flex items-start justify-between gap-3">
        <a
            href="/book/{book.id}"
            class="flex-1 min-w-0 block no-underline text-inherit"
        >
            <h3
                class="text-lg font-semibold text-gray-900 truncate"
                title={display_title}
            >
                {display_title}
            </h3>
            <p
                class="text-sm text-gray-600 mt-1 truncate"
                title={display_author}
            >
                {display_author}
            </p>
        </a>
        {#if on_delete}
            <button
                type="button"
                class={confirm_armed
                    ? "shrink-0 text-white bg-red-600 hover:bg-red-700 rounded px-3 py-2 text-sm font-semibold inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[180px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
                    : "shrink-0 text-red-700 hover:text-red-800 rounded px-3 py-2 text-sm inline-flex items-center justify-center gap-2 min-h-[44px] min-w-[180px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"}
                onclick={handle_delete}
                onkeydown={handle_keydown}
                title={confirm_armed ? "Click again to confirm delete" : "Delete book"}
                aria-label={confirm_armed ? "Click again to confirm delete" : "Delete book"}
                aria-expanded={confirm_armed}
            >
                {#if confirm_armed}
                    <IconDelete class="w-5 h-5" />
                    <span>Click again to confirm</span>
                {:else}
                    <IconDelete class="w-5 h-5" />
                    <span>Delete</span>
                {/if}
                <span
                    aria-live="polite"
                    class="sr-only"
                    >{confirm_armed ? "Click again to confirm delete" : ""}</span
                >
            </button>
        {/if}
    </div>
    <div class="mt-4 flex items-center justify-between text-sm">
        <div class="inline-flex items-center text-gray-500">
            <IconClock class="h-4 w-4 mr-1" />
            <span>{formatted_date}</span>
        </div>
        <div class="inline-flex items-center text-gray-500">
            <IconList class="h-4 w-4 mr-1" />
            <span>{book.chapter_count} chapters</span>
        </div>
    </div>
</div>
