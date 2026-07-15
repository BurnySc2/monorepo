<script lang="ts">
import type { components } from "@repo/api-types"
import { fetch_delete_file, fetch_queue_file, fetch_search, fetch_view_file } from "$lib/api"
import ColumnReorderDialog from "$lib/components/ColumnReorderDialog.svelte"
import MediaDialog from "$lib/components/MediaDialog.svelte"
import ResultsGrid from "$lib/components/ResultsGrid.svelte"
import SearchPanel from "$lib/components/SearchPanel.svelte"

type SearchResult = components["schemas"]["SearchResultItem"]

interface SearchFilters {
    search_text: string
    channel_name: string
    datetime_min: string
    datetime_max: string
    reactions_min: number
    reactions_max: number
    comments_min: number
    comments_max: number
    must_have_file: boolean
    file_extension: string
    file_duration_min: string
    file_duration_max: string
    file_size_min: number
    file_size_max: number
    file_image_width_min: number
    file_image_width_max: number
    file_image_height_min: number
    file_image_height_max: number
}

let results = $state<SearchResult[]>([])
let is_searching = $state(false)
let show_column_dialog = $state(false)
let show_media_dialog = $state(false)
let media_url = $state("")
let media_mime = $state("")

let filters = $state<SearchFilters>({
    search_text: "",
    channel_name: "",
    datetime_min: "",
    datetime_max: "",
    reactions_min: 0,
    reactions_max: 0,
    comments_min: 0,
    comments_max: 0,
    must_have_file: false,
    file_extension: "",
    file_duration_min: "00:00:00",
    file_duration_max: "00:00:00",
    file_size_min: 0,
    file_size_max: 0,
    file_image_width_min: 0,
    file_image_width_max: 0,
    file_image_height_min: 0,
    file_image_height_max: 0,
})

async function handle_search() {
    is_searching = true
    try {
        const resp = await fetch_search(new URLSearchParams(filters as unknown as Record<string, string>).toString())
        if (resp) {
            results = resp
        }
    } catch (e) {
        console.error("Search failed", e)
    } finally {
        is_searching = false
    }
}

async function handle_queue_file(id: string) {
    await fetch_queue_file(id)
}

async function handle_delete_file(id: string) {
    await fetch_delete_file(id)
}

async function handle_view_file(id: string) {
    try {
        const data = await fetch_view_file(id)
        if (data) {
            media_url = data.minio_url
            media_mime = data.mime_type
            show_media_dialog = true
        }
    } catch (e) {
        console.error("View file failed", e)
    }
}

function close_media_dialog() {
    show_media_dialog = false
    media_url = ""
    media_mime = ""
}
</script>

<main class="flex h-full flex-col items-center rounded-xl bg-gray-300">
    <div class="m-2 flex h-full flex-col gap-4 rounded-xl">
        <button
            class="h-full rounded-xl border-2 border-black p-2 hover:bg-yellow-500"
            type="button"
            onclick={() => (show_column_dialog = true)}
        >
            Column order
        </button>

        <details open>
            <summary class="select-none pb-2">Search section</summary>
            <SearchPanel {filters} />
            <button
                class="h-full grow rounded-xl border-2 border-black p-2 hover:bg-green-500"
                type="button"
                onclick={handle_search}
            >
                Search
            </button>
        </details>

        {#if is_searching}
            <div class="flex items-center justify-center p-8">
                <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
                <span class="ml-4">Searching...</span>
            </div>
        {:else if results.length > 0}
            <ResultsGrid
                {results}
                onqueue={handle_queue_file}
                ondelete={handle_delete_file}
                onview={handle_view_file}
            />
        {:else}
            <div class="flex items-center justify-center p-8 text-gray-500">
                No results yet. Run a search to see messages.
            </div>
        {/if}
    </div>
</main>

{#if show_column_dialog}
    <ColumnReorderDialog onclose={() => (show_column_dialog = false)} />
{/if}

{#if show_media_dialog}
    <MediaDialog
        url={media_url}
        mime_type={media_mime}
        onclose={close_media_dialog}
    />
{/if}
