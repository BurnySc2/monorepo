<script lang="ts">
import type { Snippet } from "svelte"

interface Props {
    tabs: Array<{ id: string; label: string }>
    active_tab: string
    children: Snippet
}

let { tabs, active_tab = $bindable(), children }: Props = $props()

const panel_id = "tab-panel"
</script>

<div class="flex flex-col gap-2">
    <div
        role="tablist"
        class="flex gap-2"
    >
        {#each tabs as tab}
            <button
                role="tab"
                id="tab-{tab.id}"
                aria-selected={active_tab === tab.id}
                aria-controls={active_tab === tab.id ? panel_id : undefined}
                class="rounded-xl border-2 border-black px-4 py-2 {active_tab === tab.id
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 hover:bg-gray-300'}"
                type="button"
                onclick={() => (active_tab = tab.id)}
            >
                {tab.label}
            </button>
        {/each}
    </div>
    <div
        role="tabpanel"
        id={panel_id}
        aria-labelledby="tab-{active_tab}"
        class="rounded-xl"
    >
        {@render children()}
    </div>
</div>
