<script lang="ts">
import type { components } from "@repo/api-types"
import { fetch_search } from "$lib/api"
import { to_sort_items } from "$lib/sort_settings.svelte"
import { search_filters } from "$lib/search_filters.svelte"
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

async function handle_search() {
    is_searching = true
    try {
        const request = {
            ...search_filters,
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
    <div class="card">
        <SearchPanel
            filters={search_filters}
            onsearch={handle_search}
        />
    </div>

    <ResultsGrid
        {results}
        {onqueue}
        {ondelete}
        {onview}
        {is_searching}
    />
</div>
