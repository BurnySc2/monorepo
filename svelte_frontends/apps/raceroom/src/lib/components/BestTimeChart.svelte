<script lang="ts">
import { Html, LayerCake, Svg } from "layercake"
import type { DriverSeries } from "$lib/types"

interface Props {
    series: DriverSeries[]
    hovered_date: Date | null
}

let { series, hovered_date }: Props = $props()

const DRIVER_COLORS = [
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

function get_color(driver_name: string, car_name: string, driving_model: string): string {
    const key = `${driver_name}-${car_name}-${driving_model}`
    let hash = 0
    for (let i = 0; i < key.length; i++) {
        hash = (hash << 5) - hash + key.charCodeAt(i)
        hash |= 0
    }
    return DRIVER_COLORS[Math.abs(hash) % DRIVER_COLORS.length]
}

function format_time(seconds: number): string {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const ms = Math.floor((seconds % 1) * 100)
    return `${mins}:${secs.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`
}

function get_data_point_x(data: DriverSeries["data"], index: number): Date {
    return data[index]?.date ?? new Date()
}

function get_data_point_y(data: DriverSeries["data"], index: number): number {
    return data[index]?.best_time ?? 0
}
</script>

<div class="chart-container">
    <LayerCake
        data={series}
        x="date"
        y="best_time"
        yDomain={[0, null]}
        xDomain={[null, null]}
        padding={{ top: 20, right: 20, bottom: 40, left: 60 }}
    >
        <Svg>
            {#each series as driver_series, i}
                <g class="series-group">
                    {#each driver_series.data as point, j}
                        {@const is_hovered = hovered_date && Math.abs(point.date.getTime() - hovered_date.getTime()) < 86400000}
                        {#if j > 0}
                            {@const prev_point = driver_series.data[j - 1]}
                            <line
                                x1={prev_point.date.getTime()}
                                y1={prev_point.best_time}
                                x2={point.date.getTime()}
                                y2={point.best_time}
                                stroke={driver_series.color}
                                stroke-width={is_hovered ? 3 : 1.5}
                                stroke-opacity={is_hovered ? 1 : 0.7}
                            />
                        {/if}
                        {#if j === 0 || j === driver_series.data.length - 1 || is_hovered}
                            <circle
                                cx={point.date.getTime()}
                                cy={point.best_time}
                                r={is_hovered ? 5 : 3}
                                fill={driver_series.color}
                                stroke={is_hovered ? "#000" : "none"}
                                stroke-width={is_hovered ? 2 : 0}
                            />
                        {/if}
                    {/each}
                </g>
            {/each}
        </Svg>

        <Html>
            {#if hovered_date}
                <div
                    class="tooltip"
                    style="left: 50%; top: 10px; transform: translateX(-50%);"
                >
                    <div class="tooltip-date">{hovered_date.toLocaleDateString()}</div>
                    <div class="tooltip-entries">
                        {#each series
                            .flatMap(s => s.data.filter(p => Math.abs(p.date.getTime() - hovered_date.getTime()) < 86400000))
                            .sort((a, b) => a.best_time - b.best_time) as point}
                            <div class="tooltip-entry">
                                <span
                                    class="tooltip-color"
                                    style="background-color: {get_color(point.driver_name, point.car_name, point.driving_model)}"
                                ></span>
                                <span class="tooltip-driver">{point.driver_name}</span>
                                <span class="tooltip-car">({point.car_name})</span>
                                <span class="tooltip-time">{format_time(point.best_time)}</span>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </Html>
    </LayerCake>
</div>

<style>
.chart-container {
    width: 100%;
    height: 400px;
    position: relative;
}

.tooltip {
    position: absolute;
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 10px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
    z-index: 100;
    pointer-events: none;
    max-height: 300px;
    overflow-y: auto;
    min-width: 250px;
}

.tooltip-date {
    font-weight: bold;
    margin-bottom: 8px;
    border-bottom: 1px solid #eee;
    padding-bottom: 4px;
}

.tooltip-entries {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.tooltip-entry {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
}

.tooltip-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}

.tooltip-driver {
    font-weight: 500;
}

.tooltip-car {
    color: #666;
    font-size: 12px;
}

.tooltip-time {
    margin-left: auto;
    font-family: monospace;
    font-weight: bold;
}
</style>
