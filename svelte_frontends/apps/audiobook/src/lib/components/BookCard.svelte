<script lang="ts">
import type { BookListItemSchema as AudiobookBook } from "@repo/api-types"

interface Props {
    book: AudiobookBook
    on_delete?: (book_id: number) => void
}

let { book, on_delete }: Props = $props()

function handle_delete(event: MouseEvent) {
    event.stopPropagation()
    if (confirm("Are you sure you want to delete this book?")) {
        on_delete?.(book.id)
    }
}

const display_title = $derived(book.custom_book_title || book.book_title)
const display_author = $derived(book.custom_book_author || book.book_author)
const formatted_date = $derived(
    new Date(book.upload_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    }),
)
</script>

<a
    href="/book/{book.id}"
    class="block bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer border border-gray-200 no-underline text-inherit"
>
    <div class="flex justify-between items-start">
        <div class="flex-1 min-w-0">
            <h3 class="text-lg font-semibold text-gray-900 truncate">{display_title}</h3>
            <p class="text-sm text-gray-600 mt-1">{display_author}</p>
        </div>
        {#if on_delete}
            <button
                class="text-red-500 hover:text-red-700 p-1 ml-2"
                onclick={handle_delete}
                title="Delete book"
            >
                <svg
                    class="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    ></path>
                </svg>
            </button>
        {/if}
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
