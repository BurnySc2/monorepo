<script lang="ts">
import { fetch_search } from "$lib/api"
import { search_filters } from "$lib/search_filters.svelte"
import { to_sort_items } from "$lib/sort_settings.svelte"
import { temp_state } from "$lib/temporary-storage.svelte"
import ResultsGrid from "./ResultsGrid.svelte"
import SearchPanel from "./SearchPanel.svelte"

interface Props {
    onqueue: (id: string) => void
    ondelete: (id: string) => void
    onview: (id: string) => void
}

let { onqueue, ondelete, onview }: Props = $props()

async function handle_search() {
    temp_state.messages.is_loading = true
    temp_state.messages.error = null
    try {
        const request = {
            ...search_filters,
            sort: to_sort_items(),
        }
        const resp = await fetch_search(request)
        if (resp) {
            temp_state.messages.results = resp
        }
    } catch (e) {
        temp_state.messages.error = e instanceof Error ? e.message : "Search failed"
        console.error("Search failed", e)
    } finally {
        temp_state.messages.is_loading = false
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
        results={temp_state.messages.results ?? []}
        {onqueue}
        {ondelete}
        {onview}
        is_searching={temp_state.messages.is_loading}
    />
</div>
