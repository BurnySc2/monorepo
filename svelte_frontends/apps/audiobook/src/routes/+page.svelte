<script lang="ts">
import type { BookListItemSchema as AudiobookBook } from "@repo/api-types"
import { Spinner } from "@repo/ui"
import * as api from "$lib/api/audiobook"
import { check_login_status } from "$lib/api/auth"
import BookCard from "$lib/components/BookCard.svelte"
import BookUpload from "$lib/components/BookUpload.svelte"

let books: AudiobookBook[] = $state([])
let is_loading = $state(true)
let is_checking_auth = $state(true)
let is_logged_in = $state(false)
let is_uploading = $state(false)

const login_url = import.meta.env.VITE_API_TARGET?.includes("localhost")
    ? "http://localhost:5173"
    : "https://login.burnysc2.xyz"

async function check_auth() {
    is_checking_auth = true
    const state = await check_login_status()
    is_logged_in = state.is_logged_in
    is_checking_auth = false
}

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

// Load auth status and books on mount
$effect(() => {
    check_auth()
    load_books()
})
</script>

<div class="container mx-auto max-w-6xl px-4 py-8">
    <h1 class="text-3xl font-bold text-center mb-4">Audiobooks</h1>
    <p class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded p-3 mb-6 text-center">
        Books and audio files may be deleted at any time without notice. Do not rely on this service for permanent
        storage.
    </p>

    {#if is_checking_auth}
        <div class="flex justify-center py-12"><Spinner /></div>
    {:else if !is_logged_in}
        <div class="text-center py-12">
            <p class="text-lg text-gray-700 mb-4">You need to log in to proceed.</p>
            <button
                onclick={() => window.location.href = login_url}
                class="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
                Log In
            </button>
        </div>
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
            <div class="flex justify-center py-12"><Spinner /></div>
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
