<script lang="ts">
    import { scaleTime, scaleLinear } from "d3-scale"
    // @ts-ignore - d3-time-format has no types
    import { timeFormat } from "d3-time-format"
    import type { DriverSeries } from "$lib/types"

    interface Props {
        series: DriverSeries[]
        hovered_date: Date | null
    }

    let { series, hovered_date }: Props = $props()

    let svg_el: SVGSVGElement | undefined = $state()
    let container_el: HTMLDivElement | undefined = $state()

    const MARGIN = { top: 20, right: 20, bottom: 40, left: 20 }
    const CIRCLE_RADIUS = 3
    const HOVERED_CIRCLE_RADIUS = 5

    function format_time(seconds: number): string {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        const ms = Math.floor((seconds % 1) * 100)
        return `${mins}:${secs.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`
    }

    function extent<T>(data: T[], accessor: (d: T) => Date): [Date, Date] {
        const values = data.map(accessor)
        const min = values.reduce((a, b) => a < b ? a : b)
        const max = values.reduce((a, b) => a > b ? a : b)
        return [min, max]
    }

    function max<T>(data: T[], accessor: (d: T) => number): number {
        return data.map(accessor).reduce((a, b) => a > b ? a : b, 0)
    }

    function min<T>(data: T[], accessor: (d: T) => number): number {
        return data.map(accessor).reduce((a, b) => a < b ? a : b, Infinity)
    }

    function render_chart() {
        if (!svg_el || !container_el || series.length === 0) return

        const container_rect = container_el.getBoundingClientRect()
        const width = container_rect.width || 800
        const height = container_rect.height || 400

        // Clear previous content
        while (svg_el.firstChild) {
            svg_el.removeChild(svg_el.firstChild)
        }

        svg_el.setAttribute("width", String(width))
        svg_el.setAttribute("height", String(height))

        const inner_width = width - MARGIN.left - MARGIN.right
        const inner_height = height - MARGIN.top - MARGIN.bottom

        // Flatten all data points for domain calculation
        const all_points = series.flatMap(s => s.data)
        if (all_points.length === 0) return

        // Create scales
        const x_extent = extent(all_points, d => d.date)
        const y_min = min(all_points, d => d.best_time)
        const y_max = max(all_points, d => d.best_time) || 100

        const x_scale = scaleTime().domain(x_extent).range([0, inner_width])
        const y_scale = scaleLinear().domain([y_min, y_max]).range([inner_height, 0])

        // Create chart group
        const g = document.createElementNS("http://www.w3.org/2000/svg", "g")
        g.setAttribute("transform", `translate(${MARGIN.left},${MARGIN.top})`)
        svg_el.appendChild(g)

        // Add X axis
        const x_axis_group = document.createElementNS("http://www.w3.org/2000/svg", "g")
        x_axis_group.setAttribute("class", "x-axis")
        x_axis_group.setAttribute("transform", `translate(0,${inner_height})`)
        g.appendChild(x_axis_group)

        // X axis ticks and labels
        const x_ticks = x_scale.ticks(6)
        x_ticks.forEach(tick => {
            const x = x_scale(tick)
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line")
            line.setAttribute("x1", String(x))
            line.setAttribute("y1", "0")
            line.setAttribute("x2", String(x))
            line.setAttribute("y2", "6")
            line.setAttribute("stroke", "#ccc")
            x_axis_group.appendChild(line)

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text")
            text.setAttribute("x", String(x))
            text.setAttribute("y", "20")
            text.setAttribute("text-anchor", "middle")
            text.setAttribute("font-size", "12")
            text.setAttribute("fill", "#666")
            text.textContent = timeFormat("%b %d")(tick)
            x_axis_group.appendChild(text)
        })

        // X axis line
        const x_line = document.createElementNS("http://www.w3.org/2000/svg", "line")
        x_line.setAttribute("x1", "0")
        x_line.setAttribute("y1", String(inner_height))
        x_line.setAttribute("x2", String(inner_width))
        x_line.setAttribute("y2", String(inner_height))
        x_line.setAttribute("stroke", "#ccc")
        x_axis_group.appendChild(x_line)

        // Draw lines for each series
        series.forEach(driver_series => {
            const color = driver_series.color
            const data = driver_series.data

            // Draw lines between points
            for (let i = 1; i < data.length; i++) {
                const prev = data[i - 1]
                const curr = data[i]
                const is_hovered = hovered_date &&
                    Math.abs(curr.date.getTime() - hovered_date.getTime()) < 86400000

                const line_el = document.createElementNS("http://www.w3.org/2000/svg", "line")
                line_el.setAttribute("x1", String(x_scale(prev.date)))
                line_el.setAttribute("y1", String(y_scale(prev.best_time)))
                line_el.setAttribute("x2", String(x_scale(curr.date)))
                line_el.setAttribute("y2", String(y_scale(curr.best_time)))
                line_el.setAttribute("stroke", color)
                line_el.setAttribute("stroke-width", is_hovered ? "3" : "1.5")
                line_el.setAttribute("stroke-opacity", is_hovered ? "1" : "0.7")
                line_el.setAttribute("fill", "none")
                g.appendChild(line_el)
            }

            // Draw circles for points
            data.forEach((point, idx) => {
                const is_first = idx === 0
                const is_last = idx === data.length - 1
                const is_hovered = hovered_date &&
                    Math.abs(point.date.getTime() - hovered_date.getTime()) < 86400000
                const show_point = is_first || is_last || is_hovered

                if (show_point) {
                    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle")
                    circle.setAttribute("cx", String(x_scale(point.date)))
                    circle.setAttribute("cy", String(y_scale(point.best_time)))
                    circle.setAttribute("r", is_hovered ? String(HOVERED_CIRCLE_RADIUS) : String(CIRCLE_RADIUS))
                    circle.setAttribute("fill", color)
                    if (is_hovered) {
                        circle.setAttribute("stroke", "#000")
                        circle.setAttribute("stroke-width", "2")
                    }
                    g.appendChild(circle)
                }
            })
        })

        // Add tooltip if hovered_date exists
        if (hovered_date) {
            const tooltip_data = series
                .flatMap(s => s.data.filter(p =>
                    Math.abs(p.date.getTime() - hovered_date.getTime()) < 86400000
                ))
                .sort((a, b) => a.best_time - b.best_time)

            if (tooltip_data.length > 0) {
                const tooltip_group = document.createElementNS("http://www.w3.org/2000/svg", "g")
                tooltip_group.setAttribute("class", "tooltip-group")
                tooltip_group.setAttribute("transform", `translate(${x_scale(hovered_date.getTime())}, 0)`)
                g.appendChild(tooltip_group)

                // Create foreignObject for HTML tooltip content
                const foreign_object = document.createElementNS("http://www.w3.org/2000/svg", "foreignObject")
                foreign_object.setAttribute("x", "-175")
                foreign_object.setAttribute("y", "0")
                foreign_object.setAttribute("width", "350")
                foreign_object.setAttribute("height", "200")
                foreign_object.setAttribute("style", "z-index: 9999; position: relative;")
                tooltip_group.appendChild(foreign_object)

                const div = document.createElement("div")
                div.className = "tooltip-content"
                div.innerHTML = `
                    <div class="tooltip-date">${timeFormat("%Y-%m-%d %H:%M:%S")(hovered_date)}</div>
                    <div class="tooltip-entries">
                        ${tooltip_data.map(point => {
                            const point_color = series.find(s =>
                                s.data.some(p => p === point)
                            )?.color ?? "#ccc"
                            return `
                                <div class="tooltip-entry">
                                    <span class="tooltip-color" style="background-color: ${point_color}"></span>
                                    <span class="tooltip-driver">${point.driver_name}</span>
                                    <span class="tooltip-car">(${point.car_name})</span>
                                    <span class="tooltip-time">${format_time(point.best_time)}</span>
                                    <span class="tooltip-lap-date">${timeFormat("%Y-%m-%d %H:%M:%S")(point.date)}</span>
                                </div>
                            `
                        }).join('')}
                    </div>
                `
                foreign_object.appendChild(div)
            }
        }
    }

    $effect(() => {
        if (svg_el && series) {
            render_chart()
        }
    })

    // Re-render on window resize
    $effect(() => {
        if (typeof window !== "undefined" && container_el) {
            const observer = new ResizeObserver(() => {
                render_chart()
            })
            observer.observe(container_el)
            return () => observer.disconnect()
        }
    })
</script>

<div bind:this={container_el} class="chart-container">
    <svg bind:this={svg_el}></svg>
</div>

<style>
    .chart-container {
        width: 100%;
        height: 400px;
        position: relative;
    }

    :global(.chart-container svg) {
        display: block;
    }

    :global(.chart-container .x-axis) {
        font-size: 12px;
    }

    :global(.chart-container .x-axis path),
    :global(.chart-container .x-axis line) {
        stroke: #ccc;
    }

    :global(.chart-container .tooltip-content) {
        background: white;
        border: 1px solid #ccc;
        border-radius: 8px;
        padding: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
        z-index: 9999;
        pointer-events: none;
        max-height: 300px;
        overflow-x: visible;
        overflow-y: auto;
        min-width: 350px;
        font-family: sans-serif;
        font-size: 13px;
    }

    :global(.chart-container .tooltip-date) {
        font-weight: bold;
        margin-bottom: 8px;
        border-bottom: 1px solid #eee;
        padding-bottom: 4px;
    }

    :global(.chart-container .tooltip-entries) {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    :global(.chart-container .tooltip-entry) {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    :global(.chart-container .tooltip-color) {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    :global(.chart-container .tooltip-driver) {
        font-weight: 500;
    }

    :global(.chart-container .tooltip-car) {
        color: #666;
        font-size: 12px;
    }

    :global(.chart-container .tooltip-time) {
        margin-left: auto;
        font-family: monospace;
        font-weight: bold;
    }

    :global(.chart-container .tooltip-lap-date) {
        font-size: 11px;
        color: #888;
        white-space: nowrap;
    }
</style>