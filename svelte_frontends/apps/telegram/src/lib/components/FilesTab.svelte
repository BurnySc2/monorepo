<script lang="ts">
import type { components } from "@repo/api-types"
import { file_column_settings } from "$lib/file_column_settings.svelte"
import { format_duration, format_file_size } from "$lib/format"
import { fetch_downloads } from "$lib/api"

type DownloadedFileItem = components["schemas"]["DownloadedFileItem"]

interface Props {
    onview: (id: string) => void
    ondelete: (id: string) => void
}

let { onview, ondelete }: Props = $props()

let downloaded_files = $state<DownloadedFileItem[]>([])
let is_loading = $state(false)
let error_message = $state<string | null>(null)

$effect(() => {
    load_downloads()
})

async function load_downloads() {
    is_loading = true
    error_message = null
    try {
        downloaded_files = await fetch_downloads()
    } catch (e) {
        error_message = e instanceof Error ? e.message : "Failed to load downloads"
    } finally {
        is_loading = false
    }
}
</script>

<div class="w-full">
    {#if is_loading}
        <div class="flex items-center justify-center p-8">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
            <span class="ml-4">Loading downloads...</span>
        </div>
    {:else if error_message}
        <div class="flex flex-col items-center justify-center gap-4 p-8">
            <div class="text-red-600">{error_message}</div>
            <button
                class="rounded-xl border-2 border-black bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                type="button"
                onclick={load_downloads}
            >
                Retry
            </button>
        </div>
    {:else if downloaded_files.length === 0}
        <div class="flex items-center justify-center p-8 text-gray-500">No downloaded files yet.</div>
    {:else}
        <div class="w-full overflow-auto rounded-xl bg-white">
            <table class="w-full border-collapse">
                <thead>
                    <tr>
                        <th class="border bg-gray-100 p-2">Actions</th>
                        {#each file_column_settings.active_columns as col}
                            <th class="whitespace-nowrap border bg-gray-100 p-2">{col.name}</th>
                        {/each}
                    </tr>
                </thead>
                <tbody>
                    {#each downloaded_files as file (file.message_id)}
                        <tr class="hover:bg-gray-50">
                            <td>
                                <div class="flex">
                                    <button
                                        class="w-8 cursor-pointer rounded-xl hover:bg-green-500"
                                        type="button"
                                        onclick={() => onview(file.message_id.toString())}
                                        title="View"
                                    >
                                        <img
                                            src="/static/play.svg"
                                            alt="View"
                                        >
                                    </button>
                                    <a
                                        class="w-8 rounded-xl hover:bg-green-500"
                                        href="/telegram-browser/download-file/{file.message_id}"
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
                                        onclick={() => ondelete(file.message_id.toString())}
                                        title="Delete"
                                    >
                                        <img
                                            src="/static/delete.svg"
                                            alt="Delete"
                                        >
                                    </button>
                                </div>
                            </td>
                            {#each file_column_settings.active_columns as col}
                                {@const value = (file as Record<string, unknown>)[col.key]}
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
    {/if}
</div>
