<script lang="ts">
import { onMount } from "svelte"
import { fetch_channel_stats } from "$lib/api"
import { temp_state } from "$lib/temporary-storage.svelte"

onMount(async () => {
    if (temp_state.channels.stats === null && !temp_state.channels.is_loading) {
        temp_state.channels.is_loading = true
        temp_state.channels.error = null
        try {
            temp_state.channels.stats = await fetch_channel_stats()
        } catch (e) {
            temp_state.channels.error = e instanceof Error ? e.message : "Failed to load channel stats"
            console.error("Failed to fetch channel stats", e)
        } finally {
            temp_state.channels.is_loading = false
        }
    }
})

function format_date(date_string: string): string {
    const date = new Date(date_string)
    return date.toISOString().split("T")[0]
}
</script>

<div class="w-full">
    {#if temp_state.channels.is_loading}
        <div class="flex items-center justify-center p-8">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
            <span class="ml-4">Loading channel stats...</span>
        </div>
    {:else if temp_state.channels.error}
        <div class="flex flex-col items-center justify-center gap-4 p-8">
            <div class="text-red-600">{temp_state.channels.error}</div>
        </div>
    {:else if temp_state.channels.stats === null || temp_state.channels.stats.length === 0}
        <div class="flex items-center justify-center p-8 text-gray-500">No channel data available.</div>
    {:else}
        <div class="w-full overflow-auto rounded-xl border border-gray-200 bg-white">
            <table class="w-full border-collapse">
                <thead>
                    <tr class="sticky top-0 z-10">
                        <th class="border border-gray-200 bg-gray-100 p-2 text-left">Channel Name</th>
                        <th class="border border-gray-200 bg-gray-100 p-2 text-left">Created</th>
                        <th class="border border-gray-200 bg-gray-100 p-2 text-right">Participants</th>
                        <th class="border border-gray-200 bg-gray-100 p-2 text-right">Messages</th>
                        <th class="border border-gray-200 bg-gray-100 p-2 text-right">Files</th>
                    </tr>
                </thead>
                <tbody>
                    {#each temp_state.channels.stats as channel (channel.channel_username)}
                        <tr class="border-t border-gray-100 hover:bg-gray-50">
                            <td class="border border-gray-200 p-2">{channel.channel_title}</td>
                            <td class="whitespace-nowrap border border-gray-200 p-2">
                                {format_date(channel.creation_date)}
                            </td>
                            <td class="border border-gray-200 p-2 text-right">{channel.participants}</td>
                            <td class="border border-gray-200 p-2 text-right">{channel.total_messages}</td>
                            <td class="border border-gray-200 p-2 text-right">{channel.total_files}</td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>
