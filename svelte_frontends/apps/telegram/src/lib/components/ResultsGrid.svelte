<script lang="ts">
import type { components } from "@repo/api-types"
import { column_settings } from "$lib/column_settings.svelte"
import { format_duration, format_file_size } from "$lib/format"

type SearchResult = components["schemas"]["SearchResultItem"]

interface Props {
    results: SearchResult[]
    onqueue: (id: string) => void
    ondelete: (id: string) => void
    onview: (id: string) => void
}

let { results, onqueue, ondelete, onview }: Props = $props()
</script>

<div class="w-full overflow-auto rounded-xl bg-white">
    <table class="w-full border-collapse">
        <thead>
            <tr>
                <th class="border bg-gray-100 p-2">Actions</th>
                {#each column_settings.active_columns as col}
                    <th class="whitespace-nowrap border bg-gray-100 p-2">{col.name}</th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#each results as row (row.metadata.id)}
                <tr class="hover:bg-gray-50">
                    <!-- Action icons -->
                    <td>
                        <div
                            id="icons-{row.metadata.id}"
                            class="flex"
                        >
                            {#if row.metadata.status === "HasFile"}
                                <button
                                    class="w-8 cursor-copy rounded-xl hover:bg-yellow-500"
                                    type="button"
                                    onclick={() => onqueue(row.metadata.id)}
                                    title="Queue file"
                                >
                                    <img
                                        src="/static/queue.svg"
                                        alt="Queue"
                                    >
                                </button>
                            {:else if row.metadata.status === "Queued" || row.metadata.status === "Downloading"}
                                <div class="w-8">
                                    <img
                                        src="/static/spinner.svg"
                                        class="w-8 animate-spin"
                                        alt="Loading"
                                    >
                                </div>
                                <button
                                    class="w-8 cursor-no-drop rounded-xl hover:bg-red-500"
                                    type="button"
                                    onclick={() => ondelete(row.metadata.id)}
                                    title="Delete"
                                >
                                    <img
                                        src="/static/delete.svg"
                                        alt="Delete"
                                    >
                                </button>
                            {:else if row.metadata.status === "Downloaded"}
                                <button
                                    class="w-8 cursor-pointer rounded-xl hover:bg-green-500"
                                    type="button"
                                    onclick={() => onview(row.metadata.id)}
                                    title="View"
                                >
                                    <img
                                        src="/static/play.svg"
                                        alt="View"
                                    >
                                </button>
                                <a
                                    class="w-8 rounded-xl hover:bg-green-500"
                                    href="/telegram-browser/download-file/{row.metadata.id}"
                                    title="Download"
                                >
                                    <img
                                        src="/static/download.svg"
                                        alt="Download"
                                    >
                                </a>
                                <button
                                    class="w-8 cursor-no-drop rounded-xl hover:bg-red-500"
                                    type="button"
                                    onclick={() => ondelete(row.metadata.id)}
                                    title="Delete"
                                >
                                    <img
                                        src="/static/delete.svg"
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
                            <td class="truncate text-center">
                                {value != null ? format_file_size(value as number) : ""}
                            </td>
                        {:else if col.key === "file_duration_seconds"}
                            <td class="truncate text-center">
                                {value != null ? format_duration(value as number) : ""}
                            </td>
                        {:else if col.key === "message_link"}
                            <td>
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
                            <td class="whitespace-nowrap">{value ?? ""}</td>
                        {:else}
                            <td class="break-all">{value ?? ""}</td>
                        {/if}
                    {/each}
                </tr>
            {/each}
        </tbody>
    </table>
</div>
