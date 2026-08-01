<script lang="ts">
import type { components } from "@repo/api-types"
import { Spinner } from "@repo/ui"
import { get_api_base } from "$lib/api"
import { column_settings } from "$lib/column_settings.svelte"
import { format_duration, format_file_size } from "$lib/format"
import {
    clear_sort,
    get_sort_direction,
    get_sort_priority,
    get_sort_tooltip,
    sort_state,
    toggle_sort,
} from "$lib/sort_settings.svelte"

type SearchResult = components["schemas"]["SearchResultItem"]

interface Props {
    results: SearchResult[]
    onqueue: (id: string) => Promise<void>
    ondelete: (id: string) => void
    onview: (id: string) => void
    is_searching: boolean
}

let { results, onqueue, ondelete, onview, is_searching }: Props = $props()

async function handle_queue(id: string) {
    try {
        await onqueue(id)
        const row = results.find((r) => r.metadata.id === id)
        if (row) {
            row.metadata.download_status = "Queued"
        }
    } catch (e) {
        console.error("Queue file failed", e)
    }
}
</script>

<div class="mb-64 w-full overflow-auto rounded-xl border border-gray-200 bg-white">
    <table class="w-full border-collapse">
        <thead>
            <tr class="sticky top-0 z-10">
                <th class="border border-gray-200 bg-gray-100 p-2">
                    <div class="flex items-center gap-1">
                        Actions
                        {#if sort_state.length > 0}
                            <button
                                class="ml-1 rounded px-1 text-xs text-gray-500 hover:bg-red-100 hover:text-red-600"
                                type="button"
                                onclick={() => clear_sort()}
                                title="Clear all sorting"
                            >
                                ✕
                            </button>
                        {/if}
                    </div>
                </th>
                {#each column_settings.active_columns as col}
                    {@const direction = get_sort_direction(col.key)}
                    {@const priority = get_sort_priority(col.key)}
                    <th
                        class="whitespace-nowrap cursor-pointer select-none border border-gray-200 p-2 {direction ? 'bg-blue-100' : 'bg-gray-100'}"
                        onclick={() => toggle_sort(col.key)}
                        title={get_sort_tooltip(col.key)}
                    >
                        {col.name}
                        {#if direction !== null}
                            <span class="ml-1 text-xs font-bold text-blue-600">
                                {direction === "asc" ? "▲" : "▼"}{priority}
                            </span>
                        {/if}
                    </th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#if is_searching}
                <tr>
                    <td colspan={column_settings.active_columns.length + 1}>
                        <div class="flex flex-col items-center justify-center gap-2 py-12">
                            <div
                                class="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"
                            ></div>
                            <span class="text-sm text-gray-500">Searching...</span>
                        </div>
                    </td>
                </tr>
            {/if}
            {#each results as row (row.metadata.id)}
                <tr class="border-t border-gray-100 hover:bg-gray-50">
                    <!-- Action icons -->
                    <td>
                        <div
                            id="icons-{row.metadata.id}"
                            class="flex items-center"
                        >
                            {#if row.metadata.status === "HasFile" && row.metadata.download_status === null}
                                <button
                                    class="w-8 cursor-copy rounded-lg transition-colors hover:bg-yellow-100"
                                    type="button"
                                    onclick={() => handle_queue(row.metadata.id)}
                                    title="Queue file"
                                >
                                    <img
                                        src="/queue.svg"
                                        alt="Queue"
                                    >
                                </button>
                            {:else if [ "Queued", "Downloading", "Failed", "GiveUp"].includes(row.metadata.download_status as string)}
                                <Spinner />
                                <button
                                    class="w-8 cursor-no-drop rounded-lg transition-colors hover:bg-red-100"
                                    type="button"
                                    onclick={() => ondelete(row.metadata.id)}
                                    title="Delete"
                                >
                                    <img
                                        src="/delete.svg"
                                        alt="Delete"
                                    >
                                </button>
                            {:else if row.metadata.download_status === "Downloaded"}
                                <button
                                    class="w-8 cursor-pointer rounded-lg transition-colors hover:bg-green-100"
                                    type="button"
                                    onclick={() => onview(row.metadata.id)}
                                    title="View"
                                >
                                    <img
                                        src="/play.svg"
                                        alt="View"
                                    >
                                </button>
                                <a
                                    class="w-8 rounded-lg transition-colors hover:bg-green-100"
                                    href={`${get_api_base()}/telegram-browser/download-file/${row.metadata.id}`}
                                    title="Download"
                                >
                                    <img
                                        src="/download.svg"
                                        alt="Download"
                                    >
                                </a>
                                <button
                                    class="w-8 cursor-no-drop rounded-lg transition-colors hover:bg-red-100"
                                    type="button"
                                    onclick={() => ondelete(row.metadata.id)}
                                    title="Delete"
                                >
                                    <img
                                        src="/delete.svg"
                                        alt="Delete"
                                    >
                                </button>
                            {/if}
                        </div>
                    </td>

                    <!-- Data columns -->
                    {#each column_settings.active_columns as col}
                        {@const value = (row as Record<string, unknown>)[col.key]}
                        {#if col.key === "file_size_bytes"}
                            <td class="truncate border-t border-gray-100 text-center">
                                {value != null ? format_file_size(value as number) : ""}
                            </td>
                        {:else if col.key === "file_duration_seconds"}
                            <td class="truncate border-t border-gray-100 text-center">
                                {value != null ? format_duration(value as number) : ""}
                            </td>
                        {:else if col.key === "message_link"}
                            <td class="border-t border-gray-100">
                                {#if value}
                                    <a
                                        href={value as string}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="truncate text-purple-600 hover:underline"
                                        >Link</a
                                    >
                                {/if}
                            </td>
                        {:else if col.key === "message_date"}
                            <td class="whitespace-nowrap border-t border-gray-100">{value ?? ""}</td>
                        {:else}
                            <td class="break-all border-t border-gray-100">{value ?? ""}</td>
                        {/if}
                    {/each}
                </tr>
            {/each}
        </tbody>
    </table>
</div>
