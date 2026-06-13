<script lang="ts">
import Highcharts from "highcharts"
import highchartsMore from "highcharts/highcharts-more.js"
import {
    EVENT_TIMELINE_OPTIONS,
    type ReplayData,
    SPENDING_OPTIONS,
    TIMELINE_OPTIONS,
    type TimelineData,
    type TimelineOption,
} from "$lib/types"
import TimingsTable from "./TimingsTable.svelte"

highchartsMore(Highcharts)

interface Props {
    real_replay_data: ReplayData
    ideal_replay_data: ReplayData
    real_replay_selected_player_id: number
    ideal_replay_selected_player_id: number
    timeline_selected: TimelineOption
}

let {
    real_replay_data,
    ideal_replay_data,
    real_replay_selected_player_id = $bindable(),
    ideal_replay_selected_player_id = $bindable(),
    timeline_selected = $bindable(),
}: Props = $props()

const SECOND = 22.4

interface MergedTimelineItem {
    1: TimelineData
    2: TimelineData
}

let merged_timelines: MergedTimelineItem[] = []
let current_chart: Highcharts.Chart | null = null

function sort_by_key<T extends object>(array: T[], key: keyof T): void {
    array.sort((a, b) => {
        const aVal = a[key] as number
        const bVal = b[key] as number
        return aVal - bVal
    })
}

function gameloop_to_time_string(gameloop: number): string {
    const seconds = gameloop / SECOND
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const secondsString = secs.toString().padStart(2, "0")
    return `${minutes}:${secondsString}`
}

function merge_timelines() {
    const merged: Array<TimelineData & { _id: number }> = []

    const replay1_gameloop = real_replay_data.timeline.at(-1)![real_replay_selected_player_id].gameloop
    const replay2_gameloop = ideal_replay_data.timeline.at(-1)![ideal_replay_selected_player_id].gameloop
    const total_gameloop = Math.min(replay1_gameloop, replay2_gameloop)

    real_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[real_replay_selected_player_id], _id: 1 })
    })
    ideal_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[ideal_replay_selected_player_id], _id: 2 })
    })

    sort_by_key(merged, "gameloop")

    let playerData1: TimelineData = real_replay_data.timeline[0][real_replay_selected_player_id]
    let playerData2: TimelineData = ideal_replay_data.timeline[0][ideal_replay_selected_player_id]

    merged_timelines = []
    merged.forEach((item) => {
        // Cut off at gameloop of last gameloop of shortest replay
        if (total_gameloop < item.gameloop) {
            return
        }
        if (item._id === 1) {
            playerData1 = item
        } else {
            playerData2 = item
        }
        merged_timelines.push({
            1: { ...playerData1 },
            2: { ...playerData2 },
        })
    })
}

function is_event_timeline(option: TimelineOption): boolean {
    return (EVENT_TIMELINE_OPTIONS as readonly string[]).includes(option)
}

function is_spending_option(option: TimelineOption): boolean {
    return (SPENDING_OPTIONS as readonly string[]).includes(option)
}

function plot_data() {
    const chartElement = document.getElementById("timelinePlot")
    if (!chartElement) {
        return
    }

    // Destroy existing chart to prevent memory leak
    if (current_chart) {
        current_chart.destroy()
        current_chart = null
    }

    if (is_spending_option(timeline_selected)) {
        plot_spending_chart(chartElement)
    } else {
        plot_arearange_chart(chartElement)
    }
}

function plot_arearange_chart(chartElement: HTMLElement) {
    const seriesData = merged_timelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1][timeline_selected], item[2][timeline_selected]]
    })

    const zones = merged_timelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        const realValue = item[1][timeline_selected]
        const idealValue = item[2][timeline_selected]
        const betterThanIdeal = realValue > idealValue
        const fillColor = betterThanIdeal ? "#C0D890" : "#ED4337"
        return { value: gameloop, fillColor }
    })

    const series: object[] = [
        {
            type: "arearange",
            name: timeline_selected,
            data: seriesData,
            zoneAxis: "x",
            zones,
        },
    ]

    if (is_event_timeline(timeline_selected)) {
        const scatterData = merged_timelines
            .filter((item) => item[1][timeline_selected] !== item[2][timeline_selected])
            .map((item) => {
                const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
                const value = Math.max(item[1][timeline_selected], item[2][timeline_selected])
                return { x: gameloop, y: value }
            })
        series.push({
            type: "scatter",
            name: "Events",
            data: scatterData,
            marker: { radius: 4, symbol: "circle" },
            color: "#000",
        })
    }

    const hc = Highcharts as unknown as {
        chart: (element: HTMLElement | string, options: object) => object
    }
    current_chart = hc.chart(chartElement, {
        chart: { zoomType: "x", type: "arearange" },
        title: { text: "" },
        plotOptions: { series: { animation: false } },
        xAxis: {
            labels: {
                formatter: function () {
                    return gameloop_to_time_string((this as unknown as { value: number }).value)
                },
            },
        },
        tooltip: {},
        series,
    }) as Highcharts.Chart
}

function plot_spending_chart(chartElement: HTMLElement) {
    const econData = merged_timelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_econ, item[2].spending_econ]
    })
    const techData = merged_timelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_tech, item[2].spending_tech]
    })
    const armyData = merged_timelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_army, item[2].spending_army]
    })

    const hc = Highcharts as unknown as {
        chart: (element: HTMLElement | string, options: object) => object
    }
    current_chart = hc.chart(chartElement, {
        chart: { zoomType: "x", type: "area" },
        title: { text: "" },
        plotOptions: {
            series: { animation: false },
            area: { stacking: "normal" },
        },
        xAxis: {
            labels: {
                formatter: function () {
                    return gameloop_to_time_string((this as unknown as { value: number }).value)
                },
            },
        },
        tooltip: {},
        series: [
            { type: "area", name: "Real - Econ", data: econData.map((d) => [d[0], d[1]]), stack: "real" },
            { type: "area", name: "Real - Tech", data: techData.map((d) => [d[0], d[1]]), stack: "real" },
            { type: "area", name: "Real - Army", data: armyData.map((d) => [d[0], d[1]]), stack: "real" },
            { type: "area", name: "Ideal - Econ", data: econData.map((d) => [d[0], d[2]]), stack: "ideal" },
            { type: "area", name: "Ideal - Tech", data: techData.map((d) => [d[0], d[2]]), stack: "ideal" },
            { type: "area", name: "Ideal - Army", data: armyData.map((d) => [d[0], d[2]]), stack: "ideal" },
        ],
    }) as Highcharts.Chart
}

$effect(() => {
    real_replay_selected_player_id
    ideal_replay_selected_player_id
    timeline_selected
    if (real_replay_data && ideal_replay_data) {
        merge_timelines()
        plot_data()
    }
})
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl">
    <div class="grid grid-cols-3 text-center">
        <select
            class="border border-gray-300 rounded px-2 py-1"
            bind:value={real_replay_selected_player_id}
        >
            {#each [real_replay_data.player1.name, real_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
        <div></div>
        <select
            class="border border-gray-300 rounded px-2 py-1"
            bind:value={ideal_replay_selected_player_id}
        >
            {#each [ideal_replay_data.player1.name, ideal_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
    </div>
    <select
        class="my-2 border border-gray-300 rounded px-2 py-1"
        bind:value={timeline_selected}
    >
        {#each TIMELINE_OPTIONS as option}
            <option value={option}>{option}</option>
        {/each}
    </select>
</div>
<div id="timelinePlot"></div>

<TimingsTable
    real_building_events={real_replay_data.building_events?.[real_replay_selected_player_id - 1] ?? []}
    ideal_building_events={ideal_replay_data.building_events?.[ideal_replay_selected_player_id - 1] ?? []}
    real_upgrade_events={real_replay_data.upgrade_events?.[real_replay_selected_player_id - 1] ?? []}
    ideal_upgrade_events={ideal_replay_data.upgrade_events?.[ideal_replay_selected_player_id - 1] ?? []}
    real_unit_events={real_replay_data.unit_events?.[real_replay_selected_player_id - 1] ?? []}
    ideal_unit_events={ideal_replay_data.unit_events?.[ideal_replay_selected_player_id - 1] ?? []}
/>
