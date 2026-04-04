<script lang="ts">
import type { BuildingEvent, UnitEvent, UpgradeEvent } from "$lib/types"

interface Props {
    real_building_events: BuildingEvent[]
    ideal_building_events: BuildingEvent[]
    real_upgrade_events: UpgradeEvent[]
    ideal_upgrade_events: UpgradeEvent[]
    real_unit_events: UnitEvent[]
    ideal_unit_events: UnitEvent[]
}

let {
    real_building_events,
    ideal_building_events,
    real_upgrade_events,
    ideal_upgrade_events,
    real_unit_events,
    ideal_unit_events,
}: Props = $props()

type TimingCategory = "expansions" | "upgrades" | "tech_buildings" | "special_units"
let selectedCategory: TimingCategory = $state("expansions")

const SECOND = 22.4

const EXPANSION_TYPES = ["Nexus", "CommandCenter", "OrbitalCommand", "PlanetaryFortress"]
const TECH_BUILDING_TYPES = [
    "TwilightCouncil",
    "DarkShrine",
    "RoboticsBay",
    "FusionCore",
    "Armory",
    "Starport",
    "Factory",
    "Barracks",
    "EngineeringBay",
]
const SPECIAL_UNIT_TYPES = ["WarpPrism", "DarkTemplar", "Oracle", "Mothership", "MothershipCore"]

interface TimingRow {
    name: string
    realTime: number | null
    idealTime: number | null
}

function gameloopToTime(gameloop: number): string {
    const seconds = gameloop / SECOND
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, "0")}`
}

function getDiff(realTime: number | null, idealTime: number | null): string {
    if (realTime === null || idealTime === null) {
        return "-"
    }
    const diff = realTime - idealTime
    const absDiff = Math.abs(diff)
    const minutes = Math.floor(absDiff / 60)
    const secs = Math.floor(absDiff % 60)
    const formatted = `${minutes}:${secs.toString().padStart(2, "0")}`
    return diff >= 0 ? `+${formatted}` : `-${formatted}`
}

function getDiffClass(realTime: number | null, idealTime: number | null): string {
    if (realTime === null || idealTime === null) {
        return "text-gray-400"
    }
    const diff = realTime - idealTime
    return diff < 0 ? "text-green-600" : diff > 0 ? "text-red-600" : "text-gray-600"
}

function getExpansions(events: BuildingEvent[]): TimingRow[] {
    const rows: TimingRow[] = []
    const expansions = events.filter((e) => EXPANSION_TYPES.some((t) => e.building_type.includes(t)))

    const secondExp = expansions.find((e) => e.count === 2)
    const thirdExp = expansions.find((e) => e.count === 3)

    if (secondExp) {
        rows.push({ name: "2nd Townhall started", realTime: secondExp.gameloop, idealTime: null })
    }
    if (thirdExp) {
        rows.push({ name: "3rd Townhall started", realTime: thirdExp.gameloop, idealTime: null })
    }

    return rows
}

function getTechBuildings(events: BuildingEvent[]): TimingRow[] {
    return events
        .filter((e) => TECH_BUILDING_TYPES.some((t) => e.building_type.includes(t)))
        .map((e) => ({
            name: e.building_type.replace(/([A-Z])/g, " $1").trim(),
            realTime: e.gameloop,
            idealTime: null,
        }))
}

function getUpgrades(events: UpgradeEvent[]): TimingRow[] {
    return events.map((e) => ({
        name: e.upgrade_type.replace(/([A-Z])/g, " $1").trim(),
        realTime: e.gameloop,
        idealTime: null,
    }))
}

function getSpecialUnits(events: UnitEvent[]): TimingRow[] {
    const rows: TimingRow[] = []
    for (const type of SPECIAL_UNIT_TYPES) {
        const first = events.find((e) => e.unit_type.includes(type))
        if (first) {
            rows.push({
                name: `First ${type.replace(/([A-Z])/g, " $1").trim()}`,
                realTime: first.gameloop,
                idealTime: null,
            })
        }
    }
    return rows
}

function mergeTimings(
    realRows: TimingRow[],
    idealRows: TimingRow[],
): { name: string; realTime: number | null; idealTime: number | null }[] {
    const merged: Map<string, TimingRow> = new Map()

    for (const row of realRows) {
        merged.set(row.name, { ...row })
    }
    for (const row of idealRows) {
        const existing = merged.get(row.name)
        if (existing) {
            existing.idealTime = row.realTime
        } else {
            merged.set(row.name, { name: row.name, realTime: null, idealTime: row.realTime })
        }
    }

    return Array.from(merged.values())
}

let timings: TimingRow[] = $derived.by(() => {
    let real: TimingRow[] = []
    let ideal: TimingRow[] = []

    switch (selectedCategory) {
        case "expansions": {
            real = getExpansions(real_building_events)
            ideal = getExpansions(ideal_building_events)
            break
        }
        case "tech_buildings": {
            real = getTechBuildings(real_building_events)
            ideal = getTechBuildings(ideal_building_events)
            break
        }
        case "upgrades": {
            real = getUpgrades(real_upgrade_events)
            ideal = getUpgrades(ideal_upgrade_events)
            break
        }
        case "special_units": {
            real = getSpecialUnits(real_unit_events)
            ideal = getSpecialUnits(ideal_unit_events)
            break
        }
    }

    return mergeTimings(real, ideal)
})
</script>

<div class="timings-table-container mt-4">
    <div class="mb-2">
        <select
            bind:value={selectedCategory}
            class="border px-2 py-1 rounded"
        >
            <option value="expansions">Expansions</option>
            <option value="upgrades">Upgrades</option>
            <option value="tech_buildings">Tech Buildings</option>
            <option value="special_units">Special Units</option>
        </select>
    </div>

    {#if timings.length > 0}
        <table class="w-full text-sm">
            <thead>
                <tr class="border-b">
                    <th class="text-left py-2 px-2">Event</th>
                    <th class="text-center py-2 px-2">Real</th>
                    <th class="text-center py-2 px-2">Ideal</th>
                    <th class="text-center py-2 px-2">Diff</th>
                </tr>
            </thead>
            <tbody>
                {#each timings as row}
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-1 px-2">{row.name}</td>
                        <td class="text-center py-1 px-2 font-mono">
                            {row.realTime !== null ? gameloopToTime(row.realTime) : "-"}
                        </td>
                        <td class="text-center py-1 px-2 font-mono">
                            {row.idealTime !== null ? gameloopToTime(row.idealTime) : "-"}
                        </td>
                        <td class="text-center py-1 px-2 font-mono {getDiffClass(row.realTime, row.idealTime)}">
                            {getDiff(row.realTime, row.idealTime)}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {:else}
        <p class="text-gray-500 text-sm py-4 text-center">No {selectedCategory} found in replay data</p>
    {/if}
</div>
