<script lang="ts">
import * as api from "$lib/api/audiobook"
import BookCard from "$lib/components/BookCard.svelte"
import BookUpload from "$lib/components/BookUpload.svelte"
import Spinner from "$lib/components/Spinner.svelte"
import type { AudiobookBook } from "$lib/types/audiobook"

let books: AudiobookBook[] = $state([])
let is_loading = $state(true)
let is_logged_in = $state(true) // TODO: Check auth status
let is_uploading = $state(false)

async function load_books() {
    is_loading = true
    try {
        books = await api.get_books()
    } catch (e) {
        console.error("Failed to load books:", e)
    } finally {
        is_loading = false
    }
}

async function handle_upload(file: File) {
    is_uploading = true
    try {
        await api.upload_epub(file)
        await load_books()
    } catch (e) {
        console.error("Failed to upload:", e)
        alert("Failed to upload book")
    } finally {
        is_uploading = false
    }
}

async function handle_delete_book(book_id: number) {
    try {
        await api.delete_book(book_id)
        books = books.filter((b) => b.id !== book_id)
    } catch (e) {
        console.error("Failed to delete book:", e)
        alert("Failed to delete book")
    }
}

// Load books on mount
$effect(() => {
    load_books()
})
</script>

<div class="container mx-auto max-w-6xl px-4 py-8">
    <h1 class="text-3xl font-bold text-center mb-4">Audiobooks</h1>
    <p class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3 mb-6 text-center">
        Books and audio files may be deleted at any time without notice. Do not rely on this service for permanent storage.
    </p>

    {#if !is_loading && !is_logged_in}
        <p class="text-center text-gray-600">Log in before you can upload books.</p>
    {:else}
        <div class="mb-8">
            <BookUpload
                on_upload={handle_upload}
                {is_uploading}
                disabled={!is_logged_in}
            />
            <p class="text-xs text-gray-500 mt-2 text-center">
                By uploading, you confirm that you own the rights to this content.
            </p>
        </div>

        {#if is_loading}
            <div class="flex justify-center py-12"><Spinner size="lg" /></div>
        {:else if books.length === 0}
            <p class="text-center text-gray-500 py-8">Your uploaded books will appear here.</p>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each books as book (book.id)}
                    <BookCard
                        {book}
                        on_delete={handle_delete_book}
                    />
                {/each}
            </div>
        {/if}
    {/if}
</div>
