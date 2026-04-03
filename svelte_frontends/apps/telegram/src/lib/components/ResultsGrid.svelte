<script lang="ts">
interface SearchResult {
    metadata: {
        id: string
        status: "HasFile" | "Queued" | "Downloading" | "Downloaded"
    }
    [key: string]: unknown
}

interface Props {
    results: SearchResult[]
    onqueue: (id: string) => void
    ondelete: (id: string) => void
    onview: (id: string) => void
}

let { results, onqueue, ondelete, onview }: Props = $props()

// Define table headers based on expected columns
const table_headers: Record<string, string> = {
    message_date: "Date",
    channel_title: "Channel",
    message_text: "Message",
    amount_of_reactions: "Reactions",
    amount_of_comments: "Comments",
    file_extension: "Ext",
    file_size_bytes: "Size",
    file_duration_seconds: "Duration",
    message_link: "Link",
}

function format_file_size(bytes: number): string {
    if (bytes === 0) {
        return "0 B"
    }
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / k ** i).toFixed(1))} ${sizes[i]}`
}

function format_duration(seconds: number): string {
    if (!seconds) {
        return ""
    }
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    if (h > 0) {
        return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`
    }
    return `${m}:${s.toString().padStart(2, "0")}`
}
</script>

<div class="w-full overflow-auto rounded-xl bg-white">
    <table class="w-full border-collapse">
        <thead>
            <tr>
                <th class="border bg-gray-100 p-2">Actions</th>
                {#each Object.entries(table_headers) as [ key, header ]}
                    <th class="whitespace-nowrap border bg-gray-100 p-2">{header}</th>
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
                    {#each Object.keys(table_headers) as col_key}
                        {@const value = row[col_key]}
                        {#if col_key === "file_size_bytes"}
                            <td class="truncate text-center">{format_file_size(value as number)}</td>
                        {:else if col_key === "file_duration_seconds"}
                            <td class="truncate text-center">{format_duration(value as number)}</td>
                        {:else if col_key === "message_link"}
                            <td>
                                <a
                                    href={value as string}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="truncate text-purple-600 hover:underline"
                                    >Link</a
                                >
                            </td>
                        {:else}
                            <td class="line-clamp-2 break-all">{value ?? ""}</td>
                        {/if}
                    {/each}
                </tr>
            {/each}
        </tbody>
    </table>
</div>
