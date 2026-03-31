<script lang="ts">
    import { page } from "$app/state";
    import type { AudiobookChapterQueryResult, AudioSettings, BookWithChapters } from "$lib/types/audiobook";
    import * as api from "$lib/api/audiobook";

    let book_id = $derived(Number(page.params.bookId));

    let book_data = $state<BookWithChapters | null>(null);
    let is_loading = $state(true);
    let user_has_access = $state(false);

    // Edit state
    let is_editing_title = $state(false);
    let is_editing_author = $state(false);
    let custom_book_title = $state("");
    let custom_book_author = $state("");

    // Audio settings
    let audio_settings = $state<AudioSettings>({
        voice: "",
        rate: 0,
        volume: 0,
        pitch: 0,
    });

    // Refresh interval
    let refresh_interval: ReturnType<typeof setInterval> | null = null;

    async function load_book() {
        is_loading = true;
        try {
            book_data = await api.get_book(book_id);
            if (book_data) {
                user_has_access = true;
                custom_book_title = book_data.book.custom_book_title || book_data.book.book_title;
                custom_book_author = book_data.book.custom_book_author || book_data.book.book_author;
                
                if (book_data.available_voices.length > 0 && !audio_settings.voice) {
                    audio_settings.voice = book_data.available_voices[0];
                }
            } else {
                user_has_access = false;
            }
        } catch (e) {
            console.error("Failed to load book:", e);
            user_has_access = false;
        } finally {
            is_loading = false;
        }
    }

    async function refresh_chapters(chapter_numbers: number[]) {
        // TODO: Call API to refresh specific chapters
        console.log("[UI] Refreshing chapters:", chapter_numbers);
    }

    async function handle_edit_title() {
        is_editing_title = !is_editing_title;
        if (!is_editing_title && custom_book_title) {
            try {
                await api.update_book_title(book_id, custom_book_title);
            } catch (e) {
                console.error("Failed to update title:", e);
            }
        }
    }

    async function handle_edit_author() {
        is_editing_author = !is_editing_author;
        if (!is_editing_author && custom_book_author) {
            try {
                await api.update_book_author(book_id, custom_book_author);
            } catch (e) {
                console.error("Failed to update author:", e);
            }
        }
    }

    async function handle_queue_chapter(chapter_id: number) {
        try {
            await api.queue_chapter_audio(chapter_id);
            await load_book();
        } catch (e) {
            console.error("Failed to queue chapter:", e);
        }
    }

    async function handle_delete_chapter_audio(chapter_id: number) {
        try {
            await api.delete_chapter_audio(chapter_id);
            await load_book();
        } catch (e) {
            console.error("Failed to delete chapter audio:", e);
        }
    }

    async function handle_queue_all() {
        try {
            await api.queue_all_chapters(book_id);
            await load_book();
        } catch (e) {
            console.error("Failed to queue all chapters:", e);
        }
    }

    async function handle_download_book() {
        try {
            const download_url = await api.download_book(book_id);
            window.location.href = download_url;
        } catch (e) {
            console.error("Failed to download book:", e);
            alert("Failed to download book - make sure all chapters have audio generated");
        }
    }

    async function handle_delete_all_audio() {
        if (!confirm("Are you sure you want to delete all audio for this book?")) return;
        try {
            await api.delete_all_audio(book_id);
            await load_book();
        } catch (e) {
            console.error("Failed to delete all audio:", e);
        }
    }

    async function handle_delete_book() {
        if (!confirm("Are you sure you want to delete this book? This cannot be undone.")) return;
        try {
            await api.delete_book(book_id);
            window.location.href = "/";
        } catch (e) {
            console.error("Failed to delete book:", e);
        }
    }

    // Start periodic refresh for queued/converting chapters
    $effect(() => {
        load_book();

        // Set up periodic refresh every 10 seconds
        refresh_interval = setInterval(() => {
            if (!is_loading && book_data) {
                const has_queued = book_data.chapters.some(c => c.number_in_queue !== null || c.is_converting);
                if (has_queued) {
                    load_book();
                }
            }
        }, 10000);

        return () => {
            if (refresh_interval) {
                clearInterval(refresh_interval);
            }
        };
    });
</script>

<div class="container">
    {#if is_loading}
        <div class="loading">
            <div class="spinner"></div>
        </div>
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
                    />
                {:else}
                    <h1>{book_data.book.custom_book_title || book_data.book.book_title}</h1>
                {/if}
                <button class="edit-button" onclick={handle_edit_title}>
                    {is_editing_title ? "Save" : "Edit"}
                </button>
            </div>
            <div class="author-row">
                {#if is_editing_author}
                    <input
                        type="text"
                        bind:value={custom_book_author}
                        class="edit-input"
                    />
                {:else}
                    <h2>{book_data.book.custom_book_author || book_data.book.book_author}</h2>
                {/if}
                <button class="edit-button" onclick={handle_edit_author}>
                    {is_editing_author ? "Save" : "Edit"}
                </button>
            </div>
        </div>

        <!-- Settings -->
        <div class="settings-box">
            <h3>Settings</h3>
            <div class="settings-grid">
                <div class="setting-row">
                    <label>Voice</label>
                    <select bind:value={audio_settings.voice}>
                        {#each book_data.available_voices as voice}
                            <option value={voice}>{voice}</option>
                        {/each}
                    </select>
                </div>
                <div class="setting-row">
                    <label>Rate</label>
                    <input type="number" bind:value={audio_settings.rate} />
                </div>
                <div class="setting-row">
                    <label>Volume</label>
                    <input type="number" bind:value={audio_settings.volume} />
                </div>
                <div class="setting-row">
                    <label>Pitch</label>
                    <input type="number" bind:value={audio_settings.pitch} />
                </div>
            </div>
            <div class="button-row">
                <button class="primary-button" onclick={handle_queue_all}>Generate audio for all chapters</button>
                <button class="primary-button" onclick={handle_download_book}>Download book</button>
                <button class="danger-button" onclick={handle_delete_all_audio}>Delete all audio</button>
                <button class="danger-button" onclick={handle_delete_book}>Delete book</button>
            </div>
        </div>

        <!-- Chapters -->
        <div class="chapters-box">
            <h3>Table of Contents</h3>
            <div class="chapters-list">
                {#each book_data.chapters as chapter}
                    <div class="chapter-row">
                        <div class="chapter-info">
                            <span class="chapter-title">'{chapter.chapter_title}' with {chapter.sentence_count} sentences</span>
                        </div>
                        <div class="chapter-actions">
                            {#if chapter.has_audio}
                                <audio controls src={chapter.minio_presigned_url} preload="metadata"></audio>
                                <button class="action-button" onclick={() => handle_delete_chapter_audio(chapter.id)}>Delete</button>
                            {:else if chapter.number_in_queue !== null}
                                <div class="status">
                                    {#if chapter.number_in_queue > 0}
                                        Queued ({chapter.number_in_queue})
                                    {:else}
                                        Queued ...
                                    {/if}
                                </div>
                                <button class="action-button" onclick={() => handle_delete_chapter_audio(chapter.id)}>Remove</button>
                            {:else if chapter.is_converting}
                                <div class="status">Generating audio ...</div>
                            {:else}
                                <button class="success-button" onclick={() => handle_queue_chapter(chapter.id)}>Generate audio</button>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
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

    .loading {
        display: flex;
        justify-content: center;
        padding: 2rem;
    }

    .message {
        text-align: center;
        color: #666;
        padding: 2rem;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .book-header {
        margin-bottom: 1.5rem;
    }

    .title-row, .author-row {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }

    .title-row h1, .author-row h2 {
        margin: 0;
    }

    .title-row h1 {
        font-size: 1.75rem;
    }

    .author-row h2 {
        font-size: 1.25rem;
        color: #555;
    }

    .edit-input {
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

    .settings-box, .chapters-box {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    .settings-box h3, .chapters-box h3 {
        margin-top: 0;
        margin-bottom: 1rem;
        text-align: center;
    }

    .settings-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
    }

    .setting-row {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .setting-row label {
        font-weight: bold;
    }

    .setting-row input, .setting-row select {
        padding: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    .button-row {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .primary-button, .success-button {
        background-color: #3498db;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        flex: 1;
    }

    .success-button {
        background-color: #27ae60;
    }

    .primary-button:hover, .success-button:hover {
        opacity: 0.9;
    }

    .danger-button {
        background-color: #e74c3c;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        flex: 1;
    }

    .danger-button:hover {
        opacity: 0.9;
    }

    .chapters-list {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .chapter-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        border-bottom: 1px solid #eee;
    }

    .chapter-info {
        flex: 1;
    }

    .chapter-title {
        word-break: break-word;
    }

    .chapter-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .chapter-actions audio {
        max-width: 200px;
    }

    .action-button {
        background: none;
        border: none;
        color: #cc0000;
        cursor: pointer;
        padding: 0.25rem 0.5rem;
    }

    .action-button:hover {
        color: #990000;
    }

    .status {
        color: #666;
        min-width: 120px;
    }
</style>