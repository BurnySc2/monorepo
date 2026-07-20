<script lang="ts">
import type { components } from "@repo/api-types"
import { onMount } from "svelte"
import { fetch_channel_stats } from "$lib/api"

type ChannelStatsItem = components["schemas"]["ChannelStatsItem"]

let channel_stats = $state<ChannelStatsItem[]>([])
let is_loading = $state(true)
let error_message = $state<string | null>(null)

onMount(async () => {
    try {
        channel_stats = await fetch_channel_stats()
    } catch (e) {
        error_message = e instanceof Error ? e.message : "Failed to load channel stats"
    } finally {
        is_loading = false
    }
})

function format_date(date_string: string): string {
    const date = new Date(date_string)
    return date.toISOString().split("T")[0]
}
</script>

<div class="w-full">
    {#if is_loading}
        <div class="flex items-center justify-center p-8">
            <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
            <span class="ml-4">Loading channel stats...</span>
        </div>
    {:else if error_message}
        <div class="flex flex-col items-center justify-center gap-4 p-8">
            <div class="text-red-600">{error_message}</div>
        </div>
    {:else if channel_stats.length === 0}
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
                    {#each channel_stats as channel (channel.channel_username)}
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
