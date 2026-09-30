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
    it.each([
        {
            name: "returns empty array when storage is empty",
            setup: (_storage: ReturnType<typeof createMockStorage>) => {},
            expected_length: 0,
            assert_extra: (_result: SavedIdealReplay[]) => {},
        },
        {
            name: "returns parsed array when storage has data",
            setup: (storage: ReturnType<typeof createMockStorage>) => {
                const savedReplay: SavedIdealReplay = {
                    name: "test",
                    replay_data: createReplayData({ player1: { name: "TestPlayer" } }),
                }
                storage.store.saved_ideal_replays = JSON.stringify([savedReplay])
            },
            expected_length: 1,
            assert_extra: (result: SavedIdealReplay[]) => {
                expect(result[0].name).toBe("test")
            },
        },
        {
            name: "handles invalid JSON gracefully",
            setup: (storage: ReturnType<typeof createMockStorage>) => {
                storage.store.saved_ideal_replays = "invalid json"
            },
            expected_length: 0,
            assert_extra: (_result: SavedIdealReplay[]) => {},
        },
    ])("$name", ({ setup, expected_length, assert_extra }) => {
        const storage = createMockStorage()
        setup(storage)
        const result = load_saved_ideals(storage)
        expect(result).toHaveLength(expected_length)
        if (expected_length === 0) {
            expect(result).toEqual([])
        }
        assert_extra(result)
    })
})

describe("save_ideal_replay", () => {
    it.each([
        {
            name: "saves new replay to storage",
            initial: [] as SavedIdealReplay[],
            save_name: "new_replay",
            save_data: () => createReplayData(),
            expected_length: 1,
            expected_name: "new_replay",
            expected_player: undefined as string | undefined,
        },
        {
            name: "updates existing replay with same name",
            initial: [
                {
                    name: "existing",
                    replay_data: createReplayData({ player1: { name: "OldName" } }),
                },
            ] as SavedIdealReplay[],
            save_name: "existing",
            save_data: () => createReplayData({ player1: { name: "NewName" } }),
            expected_length: 1,
            expected_name: "existing",
            expected_player: "NewName",
        },
        {
            name: "appends new replay when name is different",
            initial: [{ name: "existing", replay_data: createReplayData() }] as SavedIdealReplay[],
            save_name: "new_one",
            save_data: () => createReplayData(),
            expected_length: 2,
            expected_name: "new_one",
            expected_player: undefined as string | undefined,
        },
    ])("$name", ({ initial, save_name, save_data, expected_length, expected_name, expected_player }) => {
        const storage = createMockStorage()
        if (initial.length > 0) {
            storage.store.saved_ideal_replays = JSON.stringify(initial)
        }
        save_ideal_replay(save_name, save_data(), storage)
        expect(storage.store.saved_ideal_replays).toBeDefined()
        const saved = JSON.parse(storage.store.saved_ideal_replays) as SavedIdealReplay[]
        expect(saved).toHaveLength(expected_length)
        if (expected_player !== undefined) {
            const entry = saved.find((s) => s.name === save_name)
            expect(entry?.replay_data.player1.name).toBe(expected_player)
        } else {
            expect(saved.some((s) => s.name === expected_name)).toBe(true)
        }
    })
})

describe("delete_saved_ideal", () => {
    it.each([
        {
            name: "removes replay from storage",
            initial: [
                { name: "replay1", replay_data: createReplayData() },
                { name: "replay2", replay_data: createReplayData() },
            ] as SavedIdealReplay[],
            delete_name: "replay1",
            expected_length: 1,
            expected_remaining: "replay2",
        },
        {
            name: "does nothing when name does not exist",
            initial: [{ name: "replay1", replay_data: createReplayData() }] as SavedIdealReplay[],
            delete_name: "nonexistent",
            expected_length: 1,
            expected_remaining: "replay1",
        },
        {
            name: "handles empty storage",
            initial: [] as SavedIdealReplay[],
            delete_name: "any_name",
            expected_length: 0,
            expected_remaining: undefined as string | undefined,
        },
    ])("$name", ({ initial, delete_name, expected_length, expected_remaining }) => {
        const storage = createMockStorage()
        if (initial.length > 0) {
            storage.store.saved_ideal_replays = JSON.stringify(initial)
        }
        delete_saved_ideal(delete_name, storage)
        const saved = JSON.parse(storage.store.saved_ideal_replays) as SavedIdealReplay[]
        expect(saved).toHaveLength(expected_length)
        if (expected_remaining !== undefined) {
            expect(saved[0].name).toBe(expected_remaining)
        } else {
            expect(storage.store.saved_ideal_replays).toBe("[]")
        }
    })
})

describe("rename_saved_ideal", () => {
    it.each([
        {
            name: "renames existing replay",
            initial_name: "old_name",
            initial_player: "Player1",
            old_name: "old_name",
            new_name: "new_name",
            expected_name: "new_name",
            expected_player: "Player1",
        },
        {
            name: "does nothing when old name does not exist",
            initial_name: "existing",
            initial_player: "Player1",
            old_name: "nonexistent",
            new_name: "new_name",
            expected_name: "existing",
            expected_player: "Player1",
        },
        {
            name: "preserves replay data when renaming",
            initial_name: "old_name",
            initial_player: "OriginalPlayer",
            old_name: "old_name",
            new_name: "new_name",
            expected_name: "new_name",
            expected_player: "OriginalPlayer",
        },
    ])("$name", ({ initial_name, initial_player, old_name, new_name, expected_name, expected_player }) => {
        const storage = createMockStorage()
        const replay: SavedIdealReplay = {
            name: initial_name,
            replay_data: createReplayData({ player1: { name: initial_player } }),
        }
        storage.store.saved_ideal_replays = JSON.stringify([replay])
        rename_saved_ideal(old_name, new_name, storage)
        const saved = JSON.parse(storage.store.saved_ideal_replays) as SavedIdealReplay[]
        expect(saved[0].name).toBe(expected_name)
        expect(saved[0].replay_data.player1.name).toBe(expected_player)
    })
})
