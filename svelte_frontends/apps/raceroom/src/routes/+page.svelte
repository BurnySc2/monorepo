<script lang="ts">
import { onMount } from "svelte"
import { fetch_times, fetch_tracks } from "$lib/api_client"
import BestTimeChart from "$lib/components/BestTimeChart.svelte"
import type { BestTimeEntry, DateRange, DriverSeries, Track } from "$lib/types"

let tracks: Track[] = $state([])
let selectedTrackId: number | undefined = $state(undefined)
let bestTimes: BestTimeEntry[] = $state([])
let dateRange: DateRange = $state("all")
let hoveredDate: Date | null = $state(null)
let isLoading = $state(false)

const DATE_RANGE_PRESETS: { label: string; value: DateRange }[] = [
    { label: "7 days", value: "7d" },
    { label: "30 days", value: "30d" },
    { label: "90 days", value: "90d" },
    { label: "1 year", value: "1y" },
    { label: "All", value: "all" },
]

function getStartDate(range: DateRange): string | undefined {
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

function groupByDriver(data: BestTimeEntry[]): DriverSeries[] {
    const groups = new Map<string, BestTimeEntry[]>()

    for (const entry of data) {
        const key = `${entry.driver_name}-${entry.car_name}-${entry.driving_model}`
        if (!groups.has(key)) {
            groups.set(key, [])
        }
        groups.get(key)!.push(entry)
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

    let colorIndex = 0
    const result: DriverSeries[] = []

    for (const [key, entries] of groups) {
        const [driver_name, car_name, driving_model] = key.split("---")
        const sortedEntries = entries
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
            color: colors[colorIndex++ % colors.length],
            data: sortedEntries,
        })
    }

    return result
}

async function loadTracks() {
    try {
        tracks = await fetch_tracks()
        if (tracks.length > 0) {
            selectedTrackId = tracks[0].id
        }
    } catch (error) {
        console.error("Failed to load tracks:", error)
    }
}

async function loadTimes() {
    isLoading = true
    try {
        const startDate = getStartDate(dateRange)
        bestTimes = await fetch_times(selectedTrackId, startDate)
    } catch (error) {
        console.error("Failed to load times:", error)
    } finally {
        isLoading = false
    }
}

function handleMouseMove(event: MouseEvent) {
    const chartArea = (event.currentTarget as HTMLElement).querySelector(".chart-container")
    if (!chartArea) {
        return
    }

    const rect = chartArea.getBoundingClientRect()
    const x = event.clientX - rect.left
    const percentage = x / rect.width

    const allDates = bestTimes
        .filter((t) => t.date)
        .map((t) => new Date(t.date))
        .sort((a, b) => a.getTime() - b.getTime())

    if (allDates.length === 0) {
        hoveredDate = null
        return
    }

    const minDate = allDates[0].getTime()
    const maxDate = allDates[allDates.length - 1].getTime()
    const targetTime = minDate + (maxDate - minDate) * percentage

    hoveredDate = new Date(targetTime)
}

function handleMouseLeave() {
    hoveredDate = null
}

let series: DriverSeries[] = $derived(groupByDriver(bestTimes))

onMount(() => {
    loadTracks()
})

$effect(() => {
    if (selectedTrackId !== undefined) {
        loadTimes()
    }
})

$effect(() => {
    dateRange
    if (selectedTrackId !== undefined) {
        loadTimes()
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
                bind:value={selectedTrackId}
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
                    class:btn-primary={dateRange === preset.value}
                    onclick={() => (dateRange = preset.value)}
                >
                    {preset.label}
                </button>
            {/each}
        </div>
    </div>

    {#if isLoading}
        <div class="flex items-center justify-center p-8"><span>Loading...</span></div>
    {:else if bestTimes.length === 0}
        <div class="text-center p-8 text-gray-500">No data available for the selected track and period.</div>
    {:else}
        <div
            class="chart-wrapper mb-6 border border-gray-300 rounded p-4"
            onmousemove={handleMouseMove}
            onmouseleave={handleMouseLeave}
            role="img"
            aria-label="Best times line chart"
        >
            <BestTimeChart
                {series}
                {hoveredDate}
            />
        </div>

        <div class="legend mb-6 flex flex-wrap gap-4">
            {#each series as driverSeries}
                <div class="legend-item flex items-center gap-2">
                    <div
                        class="legend-color w-4 h-4 rounded"
                        style="background-color: {driverSeries.color}"
                    ></div>
                    <span class="text-sm">
                        {driverSeries.driver_name}
                        <span class="text-gray-500">({driverSeries.car_name})</span>
                    </span>
                </div>
            {/each}
        </div>
    {/if}
</div>
