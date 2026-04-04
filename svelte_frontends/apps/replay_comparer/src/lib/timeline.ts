import { EVENT_TIMELINE_OPTIONS, SPENDING_OPTIONS, type TimelineData, type TimelineOption } from "./types"

export const SECOND = 22.4

export interface MergedTimelineItem {
    1: TimelineData
    2: TimelineData
}

export function sortByKey<T extends object>(array: T[], key: keyof T): void {
    array.sort((a, b) => {
        const aVal = a[key] as number
        const bVal = b[key] as number
        return aVal - bVal
    })
}

export function gameloopToTimeString(gameloop: number): string {
    const seconds = gameloop / SECOND
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    const secondsString = secs.toString().padStart(2, "0")
    return `${minutes}:${secondsString}`
}

export function mergeTimelines(
    realReplayTimeline: TimelineData[][],
    idealReplayTimeline: TimelineData[][],
    realPlayerId: number,
    idealPlayerId: number,
): MergedTimelineItem[] {
    const merged: Array<TimelineData & { _id: number }> = []

    realReplayTimeline.forEach((item) => {
        merged.push({ ...item[realPlayerId], _id: 1 })
    })
    idealReplayTimeline.forEach((item) => {
        merged.push({ ...item[idealPlayerId], _id: 2 })
    })

    sortByKey(merged, "gameloop")

    let playerData1: TimelineData = realReplayTimeline[0][realPlayerId]
    let playerData2: TimelineData = idealReplayTimeline[0][idealPlayerId]

    const mergedTimelines: MergedTimelineItem[] = []
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
    return mergedTimelines
}

export function isEventTimeline(option: TimelineOption): boolean {
    return (EVENT_TIMELINE_OPTIONS as readonly string[]).includes(option)
}

export function isSpendingOption(option: TimelineOption): boolean {
    return (SPENDING_OPTIONS as readonly string[]).includes(option)
}
