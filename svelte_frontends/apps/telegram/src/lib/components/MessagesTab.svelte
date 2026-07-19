<script lang="ts">
import type { components } from "@repo/api-types"
import { fetch_search } from "$lib/api"
import { to_sort_items } from "$lib/sort_settings.svelte"
import type { SearchFilters } from "$lib/types"
import ResultsGrid from "./ResultsGrid.svelte"
import SearchPanel from "./SearchPanel.svelte"

type SearchResult = components["schemas"]["SearchResultItem"]

interface Props {
    onqueue: (id: string) => void
    ondelete: (id: string) => void
    onview: (id: string) => void
}

let { onqueue, ondelete, onview }: Props = $props()

let results = $state<SearchResult[]>([])
let is_searching = $state(false)

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
        const request = {
            ...filters,
            sort: to_sort_items(),
        }

        const resp = await fetch_search(request)
        if (resp) {
            results = resp
        }
    } catch (e) {
        console.error("Search failed", e)
    } finally {
        is_searching = false
    }
}
</script>

<div class="flex flex-col gap-4">
    <SearchPanel
        {filters}
        onsearch={handle_search}
    />

    <ResultsGrid
        {results}
        {onqueue}
        {ondelete}
        {onview}
        {is_searching}
    />
</div>
