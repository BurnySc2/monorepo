import type { ReplayData, SavedIdealReplay } from "./types"

const LOCAL_STORAGE_KEY = "saved_ideal_replays"

export interface StorageLike {
    getItem(key: string): string | null
    setItem(key: string, value: string): void
}

export function load_saved_ideals(storage: StorageLike = localStorage): SavedIdealReplay[] {
    const stored = storage.getItem(LOCAL_STORAGE_KEY)
    if (stored) {
        try {
            return JSON.parse(stored) as SavedIdealReplay[]
        } catch {
            return []
        }
    }
    return []
}

export function save_ideal_replay(name: string, replay_data: ReplayData, storage: StorageLike = localStorage): void {
    const ideals = load_saved_ideals(storage)
    const existing = ideals.findIndex((i) => i.name === name)
    if (existing >= 0) {
        ideals[existing].replay_data = replay_data
    } else {
        ideals.push({ name, replay_data })
    }
    storage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(ideals))
}

export function delete_saved_ideal(name: string, storage: StorageLike = localStorage): void {
    const ideals = load_saved_ideals(storage)
    const filtered = ideals.filter((i) => i.name !== name)
    storage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(filtered))
}

export function rename_saved_ideal(old_name: string, new_name: string, storage: StorageLike = localStorage): void {
    const ideals = load_saved_ideals(storage)
    const target = ideals.find((i) => i.name === old_name)
    if (target) {
        target.name = new_name
        storage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(ideals))
    }
}
