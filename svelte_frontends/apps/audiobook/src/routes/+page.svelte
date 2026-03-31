<script lang="ts">
import * as api from "$lib/api/audiobook"
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

async function handle_file_drop(event: DragEvent) {
    event.preventDefault()
    const files = event.dataTransfer?.files
    if (!files || files.length === 0) {
        return
    }

    const file = files[0]
    if (!file.name.endsWith(".epub")) {
        alert("Please drop an .epub file")
        return
    }

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

function handle_drag_over(event: DragEvent) {
    event.preventDefault()
}

function navigate_to_book(book_id: number) {
    window.location.href = `/book/${book_id}`
}

async function handle_delete_book(book_id: number, index: number) {
    if (!confirm("Are you sure you want to delete this book?")) {
        return
    }

    try {
        await api.delete_book(book_id)
        books.splice(index, 1)
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

<div class="container">
    <h1>Audiobooks</h1>

    {#if !is_loading && !is_logged_in}
        <p class="message">Log in before you can upload books.</p>
    {:else}
        <div
            class="upload-area"
            ondrop={handle_file_drop}
            ondragover={handle_drag_over}
            role="button"
            tabindex="0"
        >
            {#if is_uploading}
                <div class="spinner"></div>
                <p>Processing book...</p>
            {:else}
                <p>Drop your .epub book here to upload</p>
            {/if}
        </div>

        {#if is_loading}
            <div class="spinner"></div>
        {:else if books.length === 0}
            <p class="message">Your uploaded books will appear here.</p>
        {:else}
            <table class="books-table">
                <thead>
                    <tr>
                        <th>Upload date</th>
                        <th>Book title</th>
                        <th>Book author</th>
                        <th>Chapters</th>
                        <th>Remove Book</th>
                    </tr>
                </thead>
                <tbody>
                    {#each books as book, index}
                        <tr>
                            <td>{book.upload_date}</td>
                            <td>
                                <button
                                    class="link-button"
                                    onclick={() => navigate_to_book(book.id)}
                                >
                                    {book.custom_book_title || book.book_title}
                                </button>
                            </td>
                            <td>
                                <button
                                    class="link-button"
                                    onclick={() => navigate_to_book(book.id)}
                                >
                                    {book.custom_book_author || book.book_author}
                                </button>
                            </td>
                            <td>{book.chapter_count}</td>
                            <td>
                                <button
                                    class="delete-button"
                                    onclick={() => handle_delete_book(book.id, index)}
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        {/if}
    {/if}
</div>

<style>
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: system-ui, -apple-system, sans-serif;
}

h1 {
    text-align: center;
    margin-bottom: 2rem;
}

.message {
    text-align: center;
    color: #666;
}

.upload-area {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 3rem;
    text-align: center;
    margin-bottom: 2rem;
    cursor: pointer;
    transition:
        border-color 0.2s,
        background-color 0.2s;
}

.upload-area:hover {
    border-color: #666;
    background-color: #f9f9f9;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #3498db;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 1rem;
}

@keyframes spin {
    0% {
        transform: rotate(0deg);
    }
    100% {
        transform: rotate(360deg);
    }
}

.books-table {
    width: 100%;
    border-collapse: collapse;
}

.books-table th,
.books-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #eee;
}

.books-table th {
    font-weight: bold;
    background-color: #f9f9f9;
}

.link-button {
    background: none;
    border: none;
    color: #0066cc;
    cursor: pointer;
    text-decoration: underline;
    padding: 0;
    font: inherit;
}

.link-button:hover {
    color: #004499;
}

.delete-button {
    background: none;
    border: none;
    color: #cc0000;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
}

.delete-button:hover {
    color: #990000;
}
</style>
