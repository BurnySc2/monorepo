<script lang="ts">
import { onMount } from "svelte"
import { fetch_times, fetch_tracks } from "$lib/api_client"
import BestTimeChart from "$lib/components/BestTimeChart.svelte"
import type { BestTimeEntry, DateRange, DriverSeries, Track } from "$lib/types"

let tracks: Track[] = $state([])
let selected_track_id: number | undefined = $state(undefined)
let best_times: BestTimeEntry[] = $state([])
let date_range: DateRange = $state("all")
let hovered_date: Date | null = $state(null)
let is_loading = $state(false)

const DATE_RANGE_PRESETS: { label: string; value: DateRange }[] = [
    { label: "7 days", value: "7d" },
    { label: "30 days", value: "30d" },
    { label: "90 days", value: "90d" },
    { label: "1 year", value: "1y" },
    { label: "All", value: "all" },
]

function get_start_date(range: DateRange): string | undefined {
    const now = new Date()
    switch (range) {
        case "7d":
            return new Date(now.setDate(now.getDate() - 7)).toISOString()
        case "30d":
            return new Date(now.setDate(now.getDate() - 30)).toISOString()
        case "90d":
            return new Date(now.setDate(now.getDate() - 90)).toISOString()
        case "1y":
            return new Date(now.setFullYear(now.getFullYear() - 1)).toISOString()
        case "all":
            return undefined
    }
}

function group_by_driver(data: BestTimeEntry[]): DriverSeries[] {
    const groups = new Map<string, BestTimeEntry[]>()

    for (const entry of data) {
        const key = `${entry.driver_name}-${entry.car_name}-${entry.driving_model}`
        if (!groups.has(key)) {
            groups.set(key, [])
        }
        groups.get(key)?.push(entry)
    }

    const colors = [
        "#e6194b",
        "#3cb44b",
        "#ffe119",
        "#4363d8",
        "#f58231",
        "#911eb4",
        "#46f0f0",
        "#f032e6",
        "#bcf60c",
        "#fabebe",
        "#008080",
        "#e6beff",
        "#9a6324",
        "#fffac8",
        "#800000",
        "#aaffc3",
        "#808000",
        "#ffd8b1",
        "#000075",
        "#808080",
    ]

    let color_index = 0
    const result: DriverSeries[] = []

    for (const [key, entries] of groups) {
        const [driver_name, car_name, driving_model] = key.split("---")
        const sorted_entries = entries
            .filter((e) => e.date && e.best_time)
            .map((e) => ({
                date: new Date(e.date),
                driver_name: e.driver_name,
                car_name: e.car_name,
                driving_model: e.driving_model,
                best_time: e.best_time,
            }))
            .sort((a, b) => a.date.getTime() - b.date.getTime())

        result.push({
            driver_name,
            car_name,
            driving_model,
            color: colors[color_index++ % colors.length],
            data: sorted_entries,
        })
    }

    return result
}

async function load_tracks() {
    try {
        tracks = await fetch_tracks()
        if (tracks.length > 0) {
            selected_track_id = tracks[0].id
        }
    } catch (error) {
        console.error("Failed to load tracks:", error)
    }
}

async function load_times() {
    is_loading = true
    try {
        const start_date = get_start_date(date_range)
        best_times = await fetch_times(selected_track_id, start_date)
    } catch (error) {
        console.error("Failed to load times:", error)
    } finally {
        is_loading = false
    }
}

function handle_mouse_move(event: MouseEvent) {
    const chart_area = (event.currentTarget as HTMLElement).querySelector(".chart-container")
    if (!chart_area) {
        return
    }

    const rect = chart_area.getBoundingClientRect()
    const x = event.clientX - rect.left
    const percentage = x / rect.width

    const all_dates = best_times
        .filter((t) => t.date)
        .map((t) => new Date(t.date))
        .sort((a, b) => a.getTime() - b.getTime())

    if (all_dates.length === 0) {
        hovered_date = null
        return
    }

    const min_date = all_dates[0].getTime()
    const max_date = all_dates[all_dates.length - 1].getTime()
    const target_time = min_date + (max_date - min_date) * percentage

    hovered_date = new Date(target_time)
}

function handle_mouse_leave() {
    hovered_date = null
}

let series: DriverSeries[] = $derived(group_by_driver(best_times))

onMount(() => {
    load_tracks()
})

$effect(() => {
    if (selected_track_id !== undefined) {
        load_times()
    }
})

$effect(() => {
    date_range
    if (selected_track_id !== undefined) {
        load_times()
    }
})
</script>

<div class="max-w-5xl mx-auto p-8">
    <h1 class="text-4xl font-bold mb-6">RaceRoom Best Times</h1>

    <div class="controls mb-6 flex flex-wrap gap-4 items-center">
        <div class="flex items-center gap-2">
            <label
                for="track-select"
                class="font-medium"
                >Track:</label
            >
            <select
                id="track-select"
                class="input"
                bind:value={selected_track_id}
                disabled={tracks.length === 0}
            >
                {#each tracks as track}
                    <option value={track.id}>{track.name}</option>
                {/each}
            </select>
        </div>

        <div class="flex items-center gap-2">
            <span class="font-medium">Period:</span>
            {#each DATE_RANGE_PRESETS as preset}
                <button
                    class="btn-secondary"
                    class:btn-primary={date_range === preset.value}
                    onclick={() => (date_range = preset.value)}
                >
                    {preset.label}
                </button>
            {/each}
        </div>
    </div>

    {#if is_loading}
        <div class="flex items-center justify-center p-8"><span>Loading...</span></div>
    {:else if best_times.length === 0}
        <div class="text-center p-8 text-gray-500">No data available for the selected track and period.</div>
    {:else}
        <div
            class="chart-wrapper mb-6 border border-gray-300 rounded p-4"
            onmousemove={handle_mouse_move}
            onmouseleave={handle_mouse_leave}
            role="img"
            aria-label="Best times line chart"
        >
            <BestTimeChart
                {series}
                {hovered_date}
            />
        </div>

        <div class="legend mb-6 flex flex-wrap gap-4">
            {#each series as driver_series}
                <div class="legend-item flex items-center gap-2">
                    <div
                        class="legend-color w-4 h-4 rounded"
                        style="background-color: {driver_series.color}"
                    ></div>
                    <span class="text-sm">
                        {driver_series.driver_name}
                        <span class="text-gray-500">({driver_series.car_name})</span>
                    </span>
                </div>
            {/each}
        </div>
    {/if}
</div>
