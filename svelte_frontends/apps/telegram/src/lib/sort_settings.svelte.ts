import type { components } from "@repo/api-types"
import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

type SortItem = components["schemas"]["SortItem"]

export const SortEntrySchema = z.object({
    column_key: z.string(),
    direction: z.enum(["asc", "desc"]),
})

export type SortEntry = z.infer<typeof SortEntrySchema>

export const SortStateSchema = z.array(SortEntrySchema).default([])
export type SortState = z.infer<typeof SortStateSchema>

const STORAGE_KEY = "sort_settings"

const persisted = create_persisted_state(STORAGE_KEY, SortStateSchema, SortStateSchema.parse([]))

export const sort_state: SortState = persisted.state

export const is_loading = persisted.is_loading

export function toggle_sort(column_key: string): void {
    const existing_index = sort_state.findIndex((e) => e.column_key === column_key)

    if (existing_index === -1) {
        // Not sorted → add as DESCENDING at position 0 (highest priority)
        sort_state.splice(0, 0, { column_key, direction: "desc" })
    } else if (sort_state[existing_index].direction === "desc") {
        // DESCENDING → flip to ASCENDING
        sort_state[existing_index].direction = "asc"
    } else {
        // ASCENDING → remove from sort
        sort_state.splice(existing_index, 1)
    }
}

export function get_sort_priority(column_key: string): number {
    const index = sort_state.findIndex((e) => e.column_key === column_key)
    return index === -1 ? 0 : index + 1
}

export function get_sort_direction(column_key: string): "asc" | "desc" | null {
    const entry = sort_state.find((e) => e.column_key === column_key)
    return entry ? entry.direction : null
}

export function clear_sort(): void {
    persisted.reset()
}

export function get_sort_tooltip(column_key: string): string {
    const direction = get_sort_direction(column_key)
    const priority = get_sort_priority(column_key)
    if (direction === null) {
        return "Click to sort descending"
    }
    const dir_label = direction === "asc" ? "ascending" : "descending"
    return `Sorted ${dir_label} (priority ${priority}). Click to ${direction === "desc" ? "switch to ascending" : "remove sort"}`
}

export function to_sort_items(): SortItem[] {
    return sort_state.map((e) => ({
        column: e.column_key as SortItem["column"],
        ascending: e.direction === "asc",
    }))
}
