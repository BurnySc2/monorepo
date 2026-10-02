import type { IBuildOrderItem } from "./types.js"

export const format_time = (time_in_seconds: number): string => {
    const minutes = Math.floor(time_in_seconds / 60)
    const seconds = Math.floor(time_in_seconds % 60)
    const minutes_string = `${minutes}`
    const seconds_string = seconds.toString().padStart(2, "0")
    return `${minutes_string}:${seconds_string}`
}

export const time_string_to_number = (time_formatted: string): number => {
    const time_split = time_formatted.split(":")
    if (time_split.length !== 2) {
        return Number.NaN
    }
    const minutes = parseInt(time_split[0], 10)
    const seconds = parseInt(time_split[1], 10)
    if (!Number.isFinite(minutes) || !Number.isFinite(seconds)) {
        return Number.NaN
    }
    return minutes * 60 + seconds
}

export const text_to_build_order = (build_order_text: string): IBuildOrderItem[] => {
    const lines = build_order_text.split("\n")
    const build_order: IBuildOrderItem[] = []
    lines.forEach((line) => {
        if (line.trim() === "") {
            return
        }
        const time_and_text = line.split(" ")
        const time = time_and_text[0]
        const text = time_and_text.slice(1).join(" ")
        const parsed_time = time_string_to_number(time)
        if (!Number.isFinite(parsed_time)) {
            return
        }
        build_order.push({
            time: parsed_time,
            text: text,
        })
    })
    return build_order
}

export function format_date_timestamp(timestamp: number): string {
    const date = new Date(timestamp)
    if (Number.isNaN(date.getTime())) {
        return "Invalid Date"
    }
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}

export function format_date_string(date_string: string): string {
    const date = new Date(date_string)
    if (Number.isNaN(date.getTime())) {
        return "Invalid Date"
    }
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    })
}
