import { describe, expect, it } from "vitest"
import type { StorageLike } from "./localStorage"
import { delete_saved_ideal, load_saved_ideals, rename_saved_ideal, save_ideal_replay } from "./localStorage"
import type { ReplayData, SavedIdealReplay } from "./types"

const createReplayData = (overrides: Partial<ReplayData> = {}): ReplayData => ({
    player1: { name: "Player1" },
    player2: { name: "Player2" },
    timeline: [],
    ...overrides,
})

const createMockStorage = (): StorageLike & { store: Record<string, string> } => {
    const store: Record<string, string> = {}
    return {
        store,
        getItem: (key: string) => store[key] ?? null,
        setItem: (key: string, value: string) => {
            store[key] = value
        },
    }
}

describe("load_saved_ideals", () => {
    it("returns empty array when storage is empty", () => {
        const storage = createMockStorage()
        const result = load_saved_ideals(storage)
        expect(result).toEqual([])
    })

    it("returns parsed array when storage has data", () => {
        const storage = createMockStorage()
        const savedReplay: SavedIdealReplay = {
            name: "test",
            replay_data: createReplayData({ player1: { name: "TestPlayer" } }),
        }
        storage.store.saved_ideal_replays = JSON.stringify([savedReplay])

        const result = load_saved_ideals(storage)

        expect(result).toHaveLength(1)
        expect(result[0].name).toBe("test")
    })

    it("handles invalid JSON gracefully", () => {
        const storage = createMockStorage()
        storage.store.saved_ideal_replays = "invalid json"

        const result = load_saved_ideals(storage)

        expect(result).toEqual([])
    })
})

describe("save_ideal_replay", () => {
    it("saves new replay to storage", () => {
        const storage = createMockStorage()
        const replayData = createReplayData()

        save_ideal_replay("new_replay", replayData, storage)

        expect(storage.store.saved_ideal_replays).toBeDefined()
        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved).toHaveLength(1)
        expect(saved[0].name).toBe("new_replay")
    })

    it("updates existing replay with same name", () => {
        const storage = createMockStorage()
        const existingReplay: SavedIdealReplay = {
            name: "existing",
            replay_data: createReplayData({ player1: { name: "OldName" } }),
        }
        storage.store.saved_ideal_replays = JSON.stringify([existingReplay])

        const newReplayData = createReplayData({ player1: { name: "NewName" } })
        save_ideal_replay("existing", newReplayData, storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved).toHaveLength(1)
        expect(saved[0].replay_data.player1.name).toBe("NewName")
    })

    it("appends new replay when name is different", () => {
        const storage = createMockStorage()
        const existingReplay: SavedIdealReplay = {
            name: "existing",
            replay_data: createReplayData(),
        }
        storage.store.saved_ideal_replays = JSON.stringify([existingReplay])

        save_ideal_replay("new_one", createReplayData(), storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved).toHaveLength(2)
    })
})

describe("delete_saved_ideal", () => {
    it("removes replay from storage", () => {
        const storage = createMockStorage()
        const replay1: SavedIdealReplay = { name: "replay1", replay_data: createReplayData() }
        const replay2: SavedIdealReplay = { name: "replay2", replay_data: createReplayData() }
        storage.store.saved_ideal_replays = JSON.stringify([replay1, replay2])

        delete_saved_ideal("replay1", storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved).toHaveLength(1)
        expect(saved[0].name).toBe("replay2")
    })

    it("does nothing when name does not exist", () => {
        const storage = createMockStorage()
        const replay: SavedIdealReplay = { name: "replay1", replay_data: createReplayData() }
        storage.store.saved_ideal_replays = JSON.stringify([replay])

        delete_saved_ideal("nonexistent", storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved).toHaveLength(1)
    })

    it("handles empty storage", () => {
        const storage = createMockStorage()
        delete_saved_ideal("any_name", storage)
        expect(storage.store.saved_ideal_replays).toBe("[]")
    })
})

describe("rename_saved_ideal", () => {
    it("renames existing replay", () => {
        const storage = createMockStorage()
        const replay: SavedIdealReplay = { name: "old_name", replay_data: createReplayData() }
        storage.store.saved_ideal_replays = JSON.stringify([replay])

        rename_saved_ideal("old_name", "new_name", storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved[0].name).toBe("new_name")
    })

    it("does nothing when old name does not exist", () => {
        const storage = createMockStorage()
        const replay: SavedIdealReplay = { name: "existing", replay_data: createReplayData() }
        storage.store.saved_ideal_replays = JSON.stringify([replay])

        rename_saved_ideal("nonexistent", "new_name", storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved[0].name).toBe("existing")
    })

    it("preserves replay data when renaming", () => {
        const storage = createMockStorage()
        const replay: SavedIdealReplay = {
            name: "old_name",
            replay_data: createReplayData({ player1: { name: "OriginalPlayer" } }),
        }
        storage.store.saved_ideal_replays = JSON.stringify([replay])

        rename_saved_ideal("old_name", "new_name", storage)

        const saved = JSON.parse(storage.store.saved_ideal_replays)
        expect(saved[0].name).toBe("new_name")
        expect(saved[0].replay_data.player1.name).toBe("OriginalPlayer")
    })
})
