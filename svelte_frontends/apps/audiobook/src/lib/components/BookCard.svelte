<script lang="ts">
import type { BookListItemSchema as AudiobookBook } from "@repo/api-types"
import { format_date_string } from "@repo/sc2-utils"
import { IconDelete } from "@repo/ui"

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

const display_title = $derived(book.custom_book_title || book.book_title)
const display_author = $derived(book.custom_book_author || book.book_author)
const formatted_date = $derived(format_date_string(book.upload_date))
</script>

<div
    class="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer border border-gray-200 no-underline text-inherit relative"
>
    <a
        href="/book/{book.id}"
        class="block no-underline text-inherit"
    >
        <div class="flex justify-between items-start">
            <div class="flex-1 min-w-0 pr-10">
                <h3 class="text-lg font-semibold text-gray-900 truncate">{display_title}</h3>
                <p class="text-sm text-gray-600 mt-1">{display_author}</p>
            </div>
        </div>

        <div class="mt-4 flex items-center justify-between text-sm">
            <div class="flex items-center text-gray-500">
                <svg
                    class="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    ></path>
                </svg>
                <span>{formatted_date}</span>
            </div>
            <div class="flex items-center text-gray-500">
                <svg
                    class="w-4 h-4 mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 6h16M4 10h16M4 14h16M4 18h16"
                    ></path>
                </svg>
                <span>{book.chapter_count} chapters</span>
            </div>
        </div>
    </a>
    {#if on_delete}
        <button
            class={confirm_armed
                ? "absolute top-4 right-4 text-white bg-red-600 hover:bg-red-700 p-1 ml-2 rounded px-2 text-sm font-semibold"
                : "absolute top-4 right-4 text-red-500 hover:text-red-700 p-1 ml-2"}
            onclick={handle_delete}
            title={confirm_armed ? "Click again to confirm delete" : "Delete book"}
            aria-label={confirm_armed ? "Click again to confirm delete" : "Delete book"}
        >
            {#if confirm_armed}
                Confirm?
            {:else}
                <IconDelete class="w-5 h-5" />
            {/if}
        </button>
    {/if}
</div>
