<script lang="ts">
import type { BookWithChapters, VoiceInfo } from "@repo/api-types"
import { Spinner } from "@repo/ui"
import JSZip from "jszip"
import { page } from "$app/state"
import * as api from "$lib/api/audiobook"
import ChapterList from "$lib/components/ChapterList.svelte"

let book_id = $derived(Number(page.params.bookId))

let book_data = $state<BookWithChapters | null>(null)
let available_voices = $state<VoiceInfo[]>([])
let is_loading = $state(true)
let is_downloading = $state(false)
let user_has_access = $state(false)
// Edit state
let is_editing_title = $state(false)
let is_editing_author = $state(false)
let custom_book_title = $state("")
let custom_book_author = $state("")

// Audio settings
import { load_audio_settings, save_audio_settings } from "$lib/audio_settings.svelte"

let audio_settings = $state(load_audio_settings())

let all_chapters_have_audio = $derived(book_data?.chapters.every((c) => c.has_audio && c.minio_presigned_url) ?? false)

let all_chapters_queued_or_have_audio = $derived(
    book_data?.chapters.every((c) => c.number_in_queue !== null || c.has_audio || c.is_converting) ?? false,
)

let any_chapter_has_audio_or_queued = $derived(
    !book_data?.chapters.some(
        (c) =>
            (c.number_in_queue !== null && c.number_in_queue !== undefined && c.number_in_queue > 0) ||
            c.has_audio ||
            c.is_converting,
    ),
)

$effect(() => {
    save_audio_settings(audio_settings)
})

// Refresh interval
let refresh_interval: ReturnType<typeof setInterval> | null = null

async function load_book() {
    is_loading = true
    try {
        book_data = await api.get_book(book_id)
        available_voices = await api.get_available_voices()
        if (book_data) {
            user_has_access = true
            custom_book_title = book_data.book.custom_book_title || book_data.book.book_title
            custom_book_author = book_data.book.custom_book_author || book_data.book.book_author

            if (available_voices.length > 0) {
                const voice_value = (v: VoiceInfo) => `${v.engine}_${v.label}`
                const voice_exists = available_voices.some((v) => voice_value(v) === audio_settings.value)
                if (!audio_settings.value || !voice_exists) {
                    audio_settings.value = voice_value(available_voices[0])
                }
            }
        } else {
            user_has_access = false
        }
    } catch (e) {
        console.error("Failed to load book:", e)
        user_has_access = false
    } finally {
        is_loading = false
    }
}

async function refresh_chapters(chapter_numbers: number[]) {
    if (!book_data) {
        return
    }
    try {
        const updated_chapters = await api.refresh_chapters(book_id, chapter_numbers)
        for (const updated of updated_chapters) {
            const idx = book_data.chapters.findIndex((c) => c.id === updated.id)
            if (idx !== -1) {
                book_data.chapters[idx] = updated
            }
        }
    } catch (e) {
        console.error("Failed to refresh chapters:", e)
    }
}

async function handle_edit_title() {
    is_editing_title = !is_editing_title
    if (!is_editing_title && custom_book_title && book_data) {
        try {
            await api.update_book_title(book_id, custom_book_title)
            book_data.book.custom_book_title = custom_book_title
        } catch (e) {
            console.error("Failed to update title:", e)
        }
    }
}

async function handle_edit_author() {
    is_editing_author = !is_editing_author
    if (!is_editing_author && custom_book_author && book_data) {
        try {
            await api.update_book_author(book_id, custom_book_author)
            book_data.book.custom_book_author = custom_book_author
        } catch (e) {
            console.error("Failed to update author:", e)
        }
    }
}

async function handle_queue_chapter(chapter_id: number) {
    if (!book_data) {
        return
    }
    const chapter = book_data.chapters.find((c) => c.chapter_number === chapter_id)
    if (!chapter) {
        return
    }

    chapter.number_in_queue = -1
    chapter.is_converting = false

    try {
        await api.queue_chapter_audio(book_id, chapter_id, audio_settings)
    } catch (e) {
        console.error("Failed to queue chapter:", e)
    }
}

async function handle_delete_chapter_audio(chapter_id: number) {
    if (!book_data) {
        return
    }
    const chapter = book_data.chapters.find((c) => c.chapter_number === chapter_id)
    if (!chapter) {
        return
    }

    try {
        reset_chapters_audio([chapter_id])
        await api.delete_chapter_audio(book_id, chapter_id)
    } catch (e) {
        console.error("Failed to delete chapter audio:", e)
    }
}

async function handle_queue_all() {
    try {
        if (book_data) {
            book_data.chapters.forEach((c) => {
                c.number_in_queue = -1
                c.is_converting = false
            })
        }
        await api.queue_all_chapters(book_id, audio_settings)
    } catch (e) {
        console.error("Failed to queue all chapters:", e)
    }
}

async function handle_download_book() {
    if (!book_data || is_downloading) {
        return
    }

    const chapters_with_audio = book_data.chapters.filter((c) => c.has_audio && c.minio_presigned_url)
    if (chapters_with_audio.length === 0) {
        alert("No chapters with audio to download")
        return
    }

    is_downloading = true

    const zip = new JSZip()
    const folder = zip.folder(`${custom_book_author.slice(0, 100)}/${custom_book_title.slice(0, 200)}`)

    if (!folder) {
        is_downloading = false
        throw new Error("Failed to create zip folder")
    }

    try {
        for (const chapter of chapters_with_audio) {
            const response = await fetch(chapter.minio_presigned_url, {
                method: "GET",
                mode: "cors",
                cache: "no-cache",
            })
            if (!response.ok) {
                // RustFS returned an XML error (403, 404, etc.)
                const error_text = await response.text()
                console.error("RustFS Error XML:", error_text)
                throw new Error(`RustFS HTTP ${response.status}`)
            }
            const blob = await response.blob()
            const chapter_num = chapter.chapter_number.toString().padStart(4, "0")
            const chapter_title = chapter.chapter_title.replace(/\s+/g, "_")
            folder.file(`${chapter_num}_${chapter_title}.mp3`, blob)
        }

        const content = await zip.generateAsync({ type: "blob" })
        const url = URL.createObjectURL(content)
        const a = document.createElement("a")
        a.href = url
        a.download = `${custom_book_author.slice(0, 100)} - ${custom_book_title.slice(0, 200)}.zip`
        a.click()
        URL.revokeObjectURL(url)
        is_downloading = false
    } catch (e) {
        console.error("Failed to download book:", e)
        alert("Failed to download book")
        is_downloading = false
    }
}

function reset_chapters_audio(chapter_ids: number[]) {
    if (!book_data) {
        return
    }
    for (const chapter of book_data.chapters) {
        if (chapter_ids.includes(chapter.chapter_number)) {
            chapter.has_audio = false
            chapter.number_in_queue = null
            chapter.is_converting = false
            chapter.minio_presigned_url = ""
        }
    }
}

async function handle_delete_all_audio() {
    if (!confirm("Are you sure you want to delete all audio for this book?")) {
        return
    }
    try {
        if (book_data) {
            reset_chapters_audio(book_data.chapters.map((c) => c.chapter_number))
        }
        await api.delete_all_audio(book_id)
    } catch (e) {
        console.error("Failed to delete all audio:", e)
    }
}

async function handle_delete_book() {
    if (!confirm("Are you sure you want to delete this book? This cannot be undone.")) {
        return
    }
    try {
        await api.delete_book(book_id)
        window.location.href = "/"
    } catch (e) {
        console.error("Failed to delete book:", e)
    }
}

// Start periodic refresh for queued/converting chapters
$effect(() => {
    load_book()

    // Set up periodic refresh every 10 seconds
    refresh_interval = setInterval(() => {
        if (!is_loading && book_data) {
            const queued_chapters = book_data.chapters.filter((c) => c.number_in_queue !== null || c.is_converting)
            if (queued_chapters.length > 0) {
                const chapter_numbers = queued_chapters.map((c) => c.chapter_number)
                refresh_chapters(chapter_numbers)
            }
        }
    }, 10000)

    return () => {
        if (refresh_interval) {
            clearInterval(refresh_interval)
        }
    }
})
</script>

<div class="container">
    {#if is_loading}
        <div class="flex justify-center"><Spinner /></div>
    {:else if !user_has_access}
        <p class="message">You don't have access to this book!</p>
    {:else if book_data}
        <!-- Book Title & Author -->
        <div class="book-header">
            <div class="title-row">
                {#if is_editing_title}
                    <input
                        type="text"
                        bind:value={custom_book_title}
                        class="edit-input"
                    >
                {:else}
                    <h1>{book_data.book.custom_book_title || book_data.book.book_title}</h1>
                {/if}
                <button
                    class="edit-button"
                    onclick={handle_edit_title}
                >
                    {is_editing_title ? "Save" : "Edit"}
                </button>
            </div>
            <div class="author-row">
                {#if is_editing_author}
                    <input
                        type="text"
                        bind:value={custom_book_author}
                        class="edit-input"
                    >
                {:else}
                    <h2>{book_data.book.custom_book_author || book_data.book.book_author}</h2>
                {/if}
                <button
                    class="edit-button"
                    onclick={handle_edit_author}
                >
                    {is_editing_author ? "Save" : "Edit"}
                </button>
            </div>
        </div>

        <!-- Settings -->
        <div class="settings-box">
            <h3>Settings</h3>
            <div class="settings-grid">
                <div class="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                    <label
                        for="voice-select"
                        class="font-bold whitespace-nowrap"
                        >Voice</label
                    >
                    <select
                        id="voice-select"
                        bind:value={audio_settings.value}
                        class="flex-1 min-w-50 px-2 py-1 border border-gray-300 rounded"
                    >
                        {#each available_voices as voice}
                            <option value={`${voice.engine}_${voice.label}`}>
                                {voice.locale} {voice.engine} {voice.label} ({voice.gender})
                            </option>
                        {/each}
                    </select>
                </div>
            </div>
            <div class="flex flex-col md:flex-row gap-2 flex-wrap">
                <button
                    class="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:opacity-90 cursor-pointer"
                    onclick={handle_queue_all}
                    disabled={all_chapters_queued_or_have_audio}
                    title={all_chapters_queued_or_have_audio ? "All chapters already have audio" : ""}
                >
                    Generate audio for all chapters
                </button>
                <button
                    class="flex-1 px-3 py-2 bg-blue-500 text-white rounded hover:opacity-90 cursor-pointer relative  flex space-x-2 justify-center items-center"
                    onclick={handle_download_book}
                    disabled={is_downloading || !all_chapters_have_audio}
                    title={!all_chapters_have_audio ? "All chapters require audio" : ""}
                >
                    {#if is_downloading}
                        <Spinner />
                    {:else if !all_chapters_have_audio && all_chapters_queued_or_have_audio}
                        <Spinner />
                    {/if}
                    <div>Download book</div>
                </button>
                <button
                    class="flex-1 btn btn-danger"
                    onclick={handle_delete_all_audio}
                    disabled={any_chapter_has_audio_or_queued}
                    title={any_chapter_has_audio_or_queued ? "Delete all audio" : "No chapters have audio"}
                >
                    Delete all audio
                </button>
                <button
                    class="flex-1 btn btn-danger"
                    onclick={handle_delete_book}
                >
                    Delete book
                </button>
            </div>
        </div>

        <!-- Chapters -->
        <div class="chapters-box">
            <h3>Table of Contents</h3>
            <ChapterList
                chapters={book_data.chapters}
                on_queue_chapter={handle_queue_chapter}
                on_delete_chapter_audio={handle_delete_chapter_audio}
            />
        </div>
    {/if}
</div>

<style>
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
    font-family: system-ui, -apple-system, sans-serif;
}

.message {
    text-align: center;
    color: #666;
    padding: 2rem;
}

.book-header {
    margin-bottom: 1.5rem;
}

.title-row,
.author-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.5rem;
}

.title-row h1,
.author-row h2 {
    margin: 0;
    flex: 1;
}

.title-row h1 {
    font-size: 1.75rem;
}

.author-row h2 {
    font-size: 1.25rem;
    color: #555;
}

.edit-input {
    flex: 1;
    font-size: 1.5rem;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
}

.edit-button {
    background: none;
    border: 1px solid #ccc;
    padding: 0.25rem 0.75rem;
    cursor: pointer;
    border-radius: 4px;
}

.edit-button:hover {
    background-color: #f0f0f0;
}

.settings-box > div > button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.settings-box,
.chapters-box {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 1rem;
    margin-bottom: 1rem;
}

.settings-box h3,
.chapters-box h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    text-align: center;
}

.settings-grid {
    margin-bottom: 1rem;
}
</style>
