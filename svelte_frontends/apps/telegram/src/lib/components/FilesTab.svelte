<script lang="ts">
import { get_api_base } from "@repo/api-client"
import { IconDelete, IconDownload, IconPlay, IconQueue } from "@repo/ui"
import { fetch_downloads } from "$lib/api"
import { file_column_settings } from "$lib/file_column_settings.svelte"
import { format_duration, format_file_size, is_safe_http_url } from "$lib/format"
import { temp_state } from "$lib/temporary-storage.svelte"

interface Props {
    onview: (id: string) => void
    ondelete: (id: string) => void
}

let { onview, ondelete }: Props = $props()

$effect(() => {
    if (temp_state.files.list === null && !temp_state.files.is_loading) {
        load_downloads()
    }
})

async function load_downloads() {
    temp_state.files.is_loading = true
    temp_state.files.error = null
    try {
        temp_state.files.list = await fetch_downloads()
    } catch (e) {
        temp_state.files.error = e instanceof Error ? e.message : "Failed to load downloads"
        console.error("Failed to fetch downloads", e)
    } finally {
        temp_state.files.is_loading = false
    }
}
</script>

<div class="w-full">
    {#if temp_state.files.is_loading}
        <div class="flex items-center justify-center p-8">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
            <span class="ml-4">Loading downloads...</span>
        </div>
    {:else if temp_state.files.error}
        <div class="flex flex-col items-center justify-center gap-4 p-8">
            <div class="text-red-600">{temp_state.files.error}</div>
            <button
                class="inline-flex items-center gap-2 rounded-xl border-2 border-black bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
                type="button"
                onclick={load_downloads}
            >
                <IconQueue class="h-5 w-5" />
                <span>Retry</span>
            </button>
        </div>
    {:else if temp_state.files.list === null || temp_state.files.list.length === 0}
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
                    {#each temp_state.files.list as file (file.message_id)}
                        <tr class="hover:bg-gray-50">
                            <td>
                                <div class="flex">
                                    <button
                                        class="inline-flex w-auto cursor-pointer items-center gap-2 rounded-xl px-2 hover:bg-green-500"
                                        type="button"
                                        onclick={() => onview(file.message_id.toString())}
                                        title="View"
                                        aria-label="View"
                                    >
                                        <IconPlay class="h-5 w-5" />
                                        <span class="text-xs">View</span>
                                    </button>
                                    <a
                                        class="inline-flex w-auto items-center gap-2 rounded-xl px-2 hover:bg-green-500"
                                        href={`${get_api_base()}/telegram-browser/download-file/${encodeURIComponent(String(file.message_id))}`}
                                        title="Download"
                                        aria-label="Download"
                                        download
                                    >
                                        <IconDownload class="h-5 w-5" />
                                        <span class="text-xs">Download</span>
                                    </a>
                                    <button
                                        class="inline-flex w-auto cursor-no-drop items-center gap-2 rounded-xl px-2 hover:bg-red-500"
                                        type="button"
                                        onclick={() => ondelete(file.message_id.toString())}
                                        title="Delete"
                                        aria-label="Delete"
                                    >
                                        <IconDelete class="h-5 w-5" />
                                        <span class="text-xs">Delete</span>
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
                                        {#if is_safe_http_url(value)}
                                            <a
                                                href={value}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                class="truncate text-purple-600 hover:underline"
                                                >Link</a
                                            >
                                        {:else if value}
                                            <span class="truncate text-gray-500">{value as string}</span>
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
