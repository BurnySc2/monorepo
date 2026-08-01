<script lang="ts">
import type { components } from "@repo/api-types"
import { onMount } from "svelte"
import { fetch_channel_names } from "$lib/api"
import type { SearchFilters } from "$lib/types"

type ChannelNameItem = components["schemas"]["ChannelNameItem"]

interface Props {
    filters: SearchFilters
    onsearch: () => void
}

let { filters, onsearch }: Props = $props()

let available_channels = $state<ChannelNameItem[]>([])

onMount(async () => {
    try {
        available_channels = await fetch_channel_names()
    } catch (err) {
        console.error("Failed to fetch channel names:", err)
    }
})

function reset_duration() {
    filters.file_duration_min = "00:00:00"
    filters.file_duration_max = "00:00:00"
}
</script>

<div
    id="search-section"
    class="grid grid-cols-1 gap-3"
>
    <!-- Search text -->
    <div class="flex flex-col">
        <input
            class="input w-full bg-white text-gray-900"
            type="search"
            bind:value={filters.search_text}
            placeholder="Must contain this text"
        >
    </div>

    <!-- Channel name -->
    <div class="flex flex-col">
        <input
            class="input w-full bg-white text-gray-900"
            list="channel-names"
            type="search"
            bind:value={filters.channel_name}
            placeholder="Must be from this channel"
        >
        <datalist id="channel-names">
            {#each available_channels as channel}
                <option value={channel.channel_title}></option>
            {/each}
        </datalist>
    </div>

    <!-- Date range -->
    <fieldset class="flex h-full items-center justify-start gap-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <legend class="bg-gray-50 rounded px-1 text-sm font-medium text-gray-600">Message date range</legend>
        <input
            class="input grow text-center bg-white text-gray-900"
            type="datetime-local"
            bind:value={filters.datetime_min}
        >
        <span class="text-gray-500">to</span>
        <input
            class="input grow text-center bg-white text-gray-900"
            type="datetime-local"
            bind:value={filters.datetime_max}
        >
    </fieldset>

    <!-- Reactions -->
    <fieldset class="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <legend class="bg-gray-50 rounded px-1 text-sm font-medium text-gray-600">Amount of reactions</legend>
        <input
            class="input w-16 grow bg-white text-gray-900"
            type="number"
            min="0"
            bind:value={filters.reactions_min}
        >
        <span class="text-gray-500">to</span>
        <input
            class="input w-16 grow bg-white text-gray-900"
            type="number"
            min="0"
            bind:value={filters.reactions_max}
        >
    </fieldset>

    <!-- Comments -->
    <fieldset class="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 p-3">
        <legend class="bg-gray-50 rounded px-1 text-sm font-medium text-gray-600">Amount of comments</legend>
        <input
            class="input w-16 grow bg-white text-gray-900"
            type="number"
            min="0"
            bind:value={filters.comments_min}
        >
        <span class="text-gray-500">to</span>
        <input
            class="input w-16 grow bg-white text-gray-900"
            type="number"
            min="0"
            bind:value={filters.comments_max}
        >
    </fieldset>

    <!-- Attachment filters -->
    <fieldset class="rounded-lg border border-gray-200 bg-gray-50 p-3">
        <legend class="bg-gray-50 rounded px-1 text-sm font-medium text-gray-600">Attachment</legend>
        <div class="grid grid-cols-1 gap-2 lg:grid-cols-2">
            <!-- Must have file -->
            <fieldset class="flex items-center justify-center gap-2 rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">Must have file</legend>
                <input
                    type="checkbox"
                    class="checkbox"
                    bind:checked={filters.must_have_file}
                >
            </fieldset>

            <!-- File extension -->
            <fieldset class="flex flex-col rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">File extension ('.mp4', '.mp3', '.pdf')</legend>
                <input
                    type="search"
                    list="file-extensions"
                    bind:value={filters.file_extension}
                    class="input text-center bg-white text-gray-900"
                    placeholder=".mp4"
                >
            </fieldset>

            <!-- Duration range -->
            <fieldset class="flex flex-col rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">Duration range (hh:mm:ss)</legend>
                <div class="flex gap-2">
                    <input
                        class="input grow text-center bg-white text-gray-900"
                        type="time"
                        step="2"
                        bind:value={filters.file_duration_min}
                    >
                    <span class="text-gray-500">to</span>
                    <input
                        class="input grow text-center bg-white text-gray-900"
                        type="time"
                        step="2"
                        bind:value={filters.file_duration_max}
                    >
                </div>
                <button
                    class="btn btn-secondary mt-2 w-full text-sm"
                    type="button"
                    onclick={reset_duration}
                >
                    Reset
                </button>
            </fieldset>

            <!-- File size range (megabytes) -->
            <fieldset class="flex items-center gap-2 rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">File size range (MB)</legend>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_size_min}
                >
                <span class="text-gray-500">to</span>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_size_max}
                >
            </fieldset>

            <!-- Image width -->
            <fieldset class="flex grow items-center gap-2 rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">Image width (px)</legend>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_width_min}
                >
                <span class="text-gray-500">to</span>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_width_max}
                >
            </fieldset>

            <!-- Image height -->
            <fieldset class="flex grow items-center gap-2 rounded border border-gray-200 bg-white p-2">
                <legend class="bg-white rounded px-1 text-xs text-gray-500">Image height (px)</legend>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_height_min}
                >
                <span class="text-gray-500">to</span>
                <input
                    class="input w-16 grow bg-white text-gray-900"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_height_max}
                >
            </fieldset>
        </div>
    </fieldset>

    <button
        class="btn btn-primary w-full"
        type="button"
        onclick={onsearch}
    >
        Search
    </button>
</div>
