<script lang="ts">
import Highcharts from "highcharts"
import highchartsMore from "highcharts/highcharts-more.js"
import { type ReplayData, TIMELINE_OPTIONS, type TimelineData, type TimelineOption } from "$lib/types"

// Init "arearange" plot
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
    // Merge events of selected players from each replay
    const merged: Array<TimelineData & { _id: number }> = []

    real_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[real_replay_selected_player_id], _id: 1 })
    })
    ideal_replay_data.timeline.forEach((item) => {
        merged.push({ ...item[ideal_replay_selected_player_id], _id: 2 })
    })

    sortByKey(merged, "gameloop")

    // Pick players from merged timelines
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

function plotData() {
    const chartElement = document.getElementById("timelinePlot")
    if (!chartElement) {
        return
    }

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

    // Highcharts chart call with type workaround for Highcharts strict typing
    const hc = Highcharts as unknown as {
        chart: (element: HTMLElement | string, options: object) => object
    }
    hc.chart(chartElement, {
        chart: {
            zoomType: "x",
            type: "arearange",
        },
        title: { text: "" },
        plotOptions: {
            series: {
                animation: false,
            },
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
            {
                type: "arearange",
                name: timelineSelected,
                data: seriesData,
                zoneAxis: "x",
                zones,
            },
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
    // Re-run when these values change
    real_replay_selected_player_id
    ideal_replay_selected_player_id
    if (real_replay_data && ideal_replay_data) {
        handlePlayerChange()
    }
})

$effect(() => {
    // Re-run when timeline selection changes
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
