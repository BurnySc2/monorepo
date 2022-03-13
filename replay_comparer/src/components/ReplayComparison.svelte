<script lang="ts">
    import Highcharts from "highcharts"
    import highchartsMore from "highcharts/highcharts-more.js"
    import { onMount } from "svelte"

    // Init "arearange" plot
    highchartsMore(Highcharts)

    export let real_replay_data
    export let ideal_replay_data
    export let real_replay_selected_player_id
    export let ideal_replay_selected_player_id
    export let timelineSelected

    let mergedTimelines = []
    const second = 22.4

    onMount(() => {
        mergeTimelines()
        plotData()
    })

    const mergeTimelines = () => {
        // Merge events of selected players from each replay
        let merged = []
        real_replay_data.timeline.forEach((item) => {
            // console.log(real_replay_selected_player_id)
            // console.log(item[real_replay_selected_player_id])
            merged.push(item[real_replay_selected_player_id])
            merged[merged.length - 1]["_id"] = 1
        })
        ideal_replay_data.timeline.forEach((item) => {
            merged.push(item[ideal_replay_selected_player_id])
            merged[merged.length - 1]["_id"] = 2
        })
        sortByKey(merged, "gameloop")

        // Pick players from merged timelines
        let playerData1 = real_replay_data.timeline[0][real_replay_selected_player_id]
        let playerData2 = ideal_replay_data.timeline[0][ideal_replay_selected_player_id]
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
        // console.log(mergedTimelines)
    }

    const sortByKey = (array: object[], key: string) => {
        array.sort((a, b) => {
            return a[key] - b[key]
        })
    }

    const gameloopToTimeString = (gameloop: number) => {
        let seconds = gameloop / second
        let minutes = Math.floor(seconds / 60)
        seconds = Math.floor(seconds % 60)
        seconds = seconds.toString().padStart(2, "0")
        return `${minutes}:${seconds}`
    }

    const plotData = () => {
        const args = {
            renderTo: "timelinePlot",
            options: {
                title: { text: "" },
                chart: {
                    zoomType: "x",
                    type: "arearange",
                },
                plotOptions: {
                    series: {
                        animation: false,
                    },
                },
                xAxis: {
                    labels: {
                        formatter: function () {
                            return gameloopToTimeString(this.value)
                        },
                    },
                },
                tooltip: {
                    // TODO use custom formatter because of xAxis values
                    // formatter: function () { return `${gameloopToTimeString(this.x)}<br>Real: ${this.y}<br>Ideal: other y value here` }
                },
                series: [
                    {
                        name: timelineSelected,
                        data: mergedTimelines.map((item) => {
                            let gameloop = Math.max(item[1].gameloop, item[2].gameloop)
                            // return [gameloop, item[1][timelineSelected], item[2][timelineSelected]]
                            return [gameloop, item[1][timelineSelected], item[2][timelineSelected]]
                        }),
                        zoneAxis: "x",
                        zones: mergedTimelines.map((item, index) => {
                            let gameloop = Math.max(item[1].gameloop, item[2].gameloop)
                            let betterThanIdeal = item[1][timelineSelected] > item[2][timelineSelected]
                            let fillColor = betterThanIdeal ? "#C0D890" : "#ED4337"
                            return { value: gameloop, fillColor }
                            // return {value: gameloop, fillColor}
                        }),
                    },
                ],
            },
        }
        Highcharts.chart(args.renderTo, args.options)
    }
</script>

<div class="flex flex-col justify-center m-8 max-w-4xl">
    <div class="grid grid-cols-3 text-center">
        <select
            bind:value={real_replay_selected_player_id}
            on:change={() => {
                mergeTimelines()
                plotData()
            }}
        >
            {#each [real_replay_data.player1.name, real_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
        <div />
        <select
            bind:value={ideal_replay_selected_player_id}
            on:change={() => {
                mergeTimelines()
                plotData()
            }}
        >
            {#each [ideal_replay_data.player1.name, ideal_replay_data.player2.name] as playerName, index}
                <option value={index + 1}>{playerName}</option>
            {/each}
        </select>
    </div>
    <select class="my-2" bind:value={timelineSelected} on:change={plotData}>
        {#each timelineOptions as timelineOption}
            <option value={timelineOption}>{timelineOption}</option>
        {/each}
    </select>
</div>
<div id="timelinePlot" />
