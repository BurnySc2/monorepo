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

highchartsMore(Highcharts)

interface Props {
    real_replay_data: ReplayData
    ideal_replay_data: ReplayData
    real_replay_selected_player_id: number
    ideal_replay_selected_player_id: number
    timelineSelected: TimelineOption
}

let {
    real_replay_data,
    ideal_replay_data,
    real_replay_selected_player_id = $bindable(),
    ideal_replay_selected_player_id = $bindable(),
    timelineSelected = $bindable(),
}: Props = $props()

const SECOND = 22.4

interface MergedTimelineItem {
    1: TimelineData
    2: TimelineData
}

let mergedTimelines: MergedTimelineItem[] = $state([])

function sortByKey<T extends object>(array: T[], key: keyof T): void {
    array.sort((a, b) => {
        const aVal = a[key] as number
        const bVal = b[key] as number
        return aVal - bVal
    })
}

function gameloopToTimeString(gameloop: number): string {
    const seconds = gameloop / SECOND
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const secondsString = secs.toString().padStart(2, "0")
    return `${minutes}:${secondsString}`
}

function mergeTimelines() {
    const merged: Array<TimelineData & { _id: number }> = []

    real_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[real_replay_selected_player_id], _id: 1 })
    })
    ideal_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[ideal_replay_selected_player_id], _id: 2 })
    })

    sortByKey(merged, "gameloop")

    let playerData1: TimelineData = real_replay_data.timeline[0][real_replay_selected_player_id]
    let playerData2: TimelineData = ideal_replay_data.timeline[0][ideal_replay_selected_player_id]

    mergedTimelines = []
    merged.forEach((item) => {
        if (item._id === 1) {
            playerData1 = item
        } else {
            playerData2 = item
        }
        mergedTimelines.push({
            1: { ...playerData1 },
            2: { ...playerData2 },
        })
    })
}

function isEventTimeline(option: TimelineOption): boolean {
    return (EVENT_TIMELINE_OPTIONS as readonly string[]).includes(option)
}

function isSpendingOption(option: TimelineOption): boolean {
    return (SPENDING_OPTIONS as readonly string[]).includes(option)
}

function plotData() {
    const chartElement = document.getElementById("timelinePlot")
    if (!chartElement) {
        return
    }

    if (isSpendingOption(timelineSelected)) {
        plotSpendingChart(chartElement)
    } else {
        plotArearangeChart(chartElement)
    }
}

function plotArearangeChart(chartElement: HTMLElement) {
    const seriesData = mergedTimelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1][timelineSelected], item[2][timelineSelected]]
    })

    const zones = mergedTimelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        const realValue = item[1][timelineSelected]
        const idealValue = item[2][timelineSelected]
        const betterThanIdeal = realValue > idealValue
        const fillColor = betterThanIdeal ? "#C0D890" : "#ED4337"
        return { value: gameloop, fillColor }
    })

    const series: object[] = [
        {
            type: "arearange",
            name: timelineSelected,
            data: seriesData,
            zoneAxis: "x",
            zones,
        },
    ]

    if (isEventTimeline(timelineSelected)) {
        const scatterData = mergedTimelines
            .filter((item) => item[1][timelineSelected] !== item[2][timelineSelected])
            .map((item) => {
                const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
                const value = Math.max(item[1][timelineSelected], item[2][timelineSelected])
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
    hc.chart(chartElement, {
        chart: { zoomType: "x", type: "arearange" },
        title: { text: "" },
        plotOptions: { series: { animation: false } },
        xAxis: {
            labels: {
                formatter: function () {
                    return gameloopToTimeString((this as unknown as { value: number }).value)
                },
            },
        },
        tooltip: {},
        series,
    })
}

function plotSpendingChart(chartElement: HTMLElement) {
    const econData = mergedTimelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_econ, item[2].spending_econ]
    })
    const techData = mergedTimelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_tech, item[2].spending_tech]
    })
    const armyData = mergedTimelines.map((item) => {
        const gameloop = Math.max(item[1].gameloop, item[2].gameloop)
        return [gameloop, item[1].spending_army, item[2].spending_army]
    })

    const hc = Highcharts as unknown as {
        chart: (element: HTMLElement | string, options: object) => object
    }
    hc.chart(chartElement, {
        chart: { zoomType: "x", type: "area" },
        title: { text: "" },
        plotOptions: {
            series: { animation: false },
            area: { stacking: "normal" },
        },
        xAxis: {
            labels: {
                formatter: function () {
                    return gameloopToTimeString((this as unknown as { value: number }).value)
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
    })
}

function handlePlayerChange() {
    mergeTimelines()
    plotData()
}

function handleTimelineChange() {
    plotData()
}

$effect(() => {
    real_replay_selected_player_id
    ideal_replay_selected_player_id
    if (real_replay_data && ideal_replay_data) {
        handlePlayerChange()
    }
})

$effect(() => {
    timelineSelected
    if (mergedTimelines.length > 0) {
        handleTimelineChange()
    }
})
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl">
    <div class="grid grid-cols-3 text-center">
        <select
            bind:value={real_replay_selected_player_id}
            onchange={handlePlayerChange}
        >
            {#each [real_replay_data.player1.name, real_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
        <div></div>
        <select
            bind:value={ideal_replay_selected_player_id}
            onchange={handlePlayerChange}
        >
            {#each [ideal_replay_data.player1.name, ideal_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
    </div>
    <select
        class="my-2"
        bind:value={timelineSelected}
    >
        {#each TIMELINE_OPTIONS as option}
            <option value={option}>{option}</option>
        {/each}
    </select>
</div>
<div id="timelinePlot"></div>
