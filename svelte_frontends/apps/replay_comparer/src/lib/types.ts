export interface TimelineData {
    gameloop: number
    workers_active: number
    workers_produced: number
    workers_lost: number
    supply: number
    supply_cap: number
    supply_block: number
    spm: number
    total_army_value: number
    total_resources_lost: number
    total_resources_collected: number
    workers_killed: number
    resource_collection_rate_all: number
    _id?: number
}

export interface Player {
    name: string
    [key: string]: unknown
}

export interface ReplayData {
    player1: Player
    player2: Player
    timeline: TimelineData[][]
}

export const TIMELINE_OPTIONS = [
    "workers_active",
    "workers_produced",
    "workers_lost",
    "supply",
    "supply_cap",
    "supply_block",
    "spm",
    "total_army_value",
    "total_resources_lost",
    "total_resources_collected",
    "workers_killed",
    "resource_collection_rate_all",
] as const

export type TimelineOption = (typeof TIMELINE_OPTIONS)[number]
