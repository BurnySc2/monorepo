<script lang="ts">
import type { SearchFilters } from "$lib/types"

interface Props {
    filters: SearchFilters
    onsearch: () => void
}

let { filters, onsearch }: Props = $props()

function reset_duration() {
    filters.file_duration_min = "00:00:00"
    filters.file_duration_max = "00:00:00"
}
</script>

<div
    id="search-section"
    class="grid grid-cols-1 gap-2 rounded-xl ring-2 ring-neutral-500 ring-offset-2"
>
    <!-- Search text -->
    <div class="flex flex-col">
        <input
            class="h-full border border-black"
            type="search"
            bind:value={filters.search_text}
            placeholder="Must contain this text"
        >
    </div>

    <!-- Channel name -->
    <div class="flex flex-col">
        <input
            class="h-full border border-black"
            list="channel-names"
            type="search"
            bind:value={filters.channel_name}
            placeholder="Must be from this channel"
        >
    </div>

    <!-- Date range -->
    <fieldset class="flex h-full items-center justify-start gap-2 rounded-xl border border-black">
        <legend class="text-center">Date range</legend>
        <input
            class="grow rounded-xl px-2 text-center"
            type="datetime-local"
            bind:value={filters.datetime_min}
        >
        <span>to</span>
        <input
            class="grow rounded-xl px-2 text-center"
            type="datetime-local"
            bind:value={filters.datetime_max}
        >
    </fieldset>

    <!-- Reactions -->
    <fieldset class="flex gap-2 rounded-xl border border-black">
        <legend class="text-center">Amount of reactions</legend>
        <input
            class="w-8 grow rounded-xl px-2"
            type="number"
            min="0"
            bind:value={filters.reactions_min}
        >
        <span>to</span>
        <input
            class="w-8 grow rounded-xl px-2"
            type="number"
            min="0"
            bind:value={filters.reactions_max}
        >
    </fieldset>

    <!-- Comments -->
    <fieldset class="flex gap-2 rounded-xl border border-black">
        <legend class="text-center">Amount of comments</legend>
        <input
            class="w-8 grow rounded-xl px-2"
            type="number"
            min="0"
            bind:value={filters.comments_min}
        >
        <span>to</span>
        <input
            class="w-8 grow rounded-xl px-2"
            type="number"
            min="0"
            bind:value={filters.comments_max}
        >
    </fieldset>

    <!-- Attachment filters -->
    <fieldset class="h-full rounded-xl border border-black p-2">
        <legend class="text-center">Attachment</legend>
        <div class="grid grid-cols-1 gap-2 lg:grid-cols-2">
            <!-- Must have file -->
            <fieldset class="flex items-center justify-center gap-2 border border-black">
                <legend class="text-center">Must have file</legend>
                <input
                    type="checkbox"
                    bind:checked={filters.must_have_file}
                >
            </fieldset>

            <!-- File extension -->
            <fieldset class="flex flex-col border border-black">
                <legend class="text-center">File extension</legend>
                <input
                    type="search"
                    list="file-extensions"
                    bind:value={filters.file_extension}
                    class="text-center"
                    placeholder="File extension"
                >
            </fieldset>

            <!-- Duration range -->
            <fieldset class="flex flex-col border border-black">
                <legend class="text-center">Duration range</legend>
                <div class="flex gap-2">
                    <input
                        class="grow text-center"
                        type="time"
                        step="2"
                        bind:value={filters.file_duration_min}
                    >
                    <span>to</span>
                    <input
                        class="grow text-center"
                        type="time"
                        step="2"
                        bind:value={filters.file_duration_max}
                    >
                </div>
                <button
                    class="h-full hover:bg-blue-300"
                    type="button"
                    onclick={reset_duration}
                >
                    Reset
                </button>
            </fieldset>

            <!-- File size range (megabytes) -->
            <fieldset class="flex items-center gap-2 border border-black">
                <legend class="text-center">File size range (MB)</legend>
                <input
                    class="w-16 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_size_min}
                >
                <span>to</span>
                <input
                    class="w-16 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_size_max}
                >
            </fieldset>

            <!-- Image width -->
            <fieldset class="flex grow gap-2 border-b border-t border-black">
                <legend class="text-center">Image width</legend>
                <input
                    class="w-8 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_width_min}
                >
                <span>to</span>
                <input
                    class="w-8 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_width_max}
                >
            </fieldset>

            <!-- Image height -->
            <fieldset class="flex grow gap-2 border-b border-t border-black">
                <legend class="text-center">Image height</legend>
                <input
                    class="w-8 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_height_min}
                >
                <span>to</span>
                <input
                    class="w-8 grow"
                    type="number"
                    min="0"
                    bind:value={filters.file_image_height_max}
                >
            </fieldset>
        </div>
    </fieldset>

    <button
        class="h-full grow rounded-xl border-2 border-black p-2 hover:bg-green-500"
        type="button"
        onclick={onsearch}
    >
        Search
    </button>
</div>
