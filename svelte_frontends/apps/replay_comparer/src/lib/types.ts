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
    army_lost: number
    active_army: number
    buildings_started: number
    building_count: number
    upgrades_completed: number
    spending_econ: number
    spending_tech: number
    spending_army: number
    spending_total: number
    unit_count: number
    _id?: number
}

export interface BuildingEvent {
    gameloop: number
    building_type: string
    count: number
}

export interface UpgradeEvent {
    gameloop: number
    upgrade_type: string
}

export interface UnitEvent {
    gameloop: number
    unit_type: string
    count: number
}

export interface Player {
    name: string
    [key: string]: unknown
}

export interface ReplayData {
    player1: Player
    player2: Player
    timeline: TimelineData[][]
    building_events?: BuildingEvent[][]
    upgrade_events?: UpgradeEvent[][]
    unit_events?: UnitEvent[][]
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
    "army_lost",
    "active_army",
    "buildings_started",
    "building_count",
    "upgrades_completed",
    "spending_econ",
    "spending_tech",
    "spending_army",
    "spending_total",
    "unit_count",
] as const

export type TimelineOption = (typeof TIMELINE_OPTIONS)[number]

export interface SavedIdealReplay {
    name: string
    replay_data: ReplayData
}

export const EVENT_TIMELINE_OPTIONS = ["buildings_started", "upgrades_completed"] as const
export type EventTimelineOption = (typeof EVENT_TIMELINE_OPTIONS)[number]

export const SPENDING_OPTIONS = ["spending_econ", "spending_tech", "spending_army"] as const
export type SpendingOption = (typeof SPENDING_OPTIONS)[number]
