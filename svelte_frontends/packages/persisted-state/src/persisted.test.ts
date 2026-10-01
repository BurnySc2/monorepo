import { beforeEach, describe, expect, it, vi } from "vitest"
import { z } from "zod"
import { create_persisted_state } from "./persisted.svelte.js"

const TestSchema = z.object({
    count: z.number().default(0),
    name: z.string().default("hello"),
})

function stub_browser_storage(initial: Record<string, string>) {
    const store = new Map<string, string>(Object.entries(initial))
    const getItem = vi.fn((key: string) => store.get(key) ?? null)
    const setItem = vi.fn((key: string, value: string) => {
        store.set(key, value)
    })
    const removeItem = vi.fn((key: string) => {
        store.delete(key)
    })
    vi.stubGlobal("window", {})
    vi.stubGlobal("localStorage", { getItem, setItem, removeItem, clear: () => store.clear() })
    return { store, getItem, setItem, removeItem }
}

beforeEach(() => {
    vi.unstubAllGlobals()
})

describe("create_persisted_state", () => {
    it("loads valid stored value on init", async () => {
        stub_browser_storage({ test_valid: JSON.stringify({ count: 5, name: "world" }) })

        const result = create_persisted_state("test_valid", TestSchema, TestSchema.parse({}))

        await new Promise((resolve) => setTimeout(resolve, 0))

        expect(result.state.count).toBe(5)
        expect(result.state.name).toBe("world")
        expect(result.is_loading.value).toBe(false)
    })

    it("falls back to initial and removes corrupt value", async () => {
        const { removeItem } = stub_browser_storage({ test_corrupt: "{not-json" })

        const result = create_persisted_state("test_corrupt", TestSchema, TestSchema.parse({}))

        await new Promise((resolve) => setTimeout(resolve, 0))

        expect(result.state.count).toBe(0)
        expect(result.state.name).toBe("hello")
        expect(removeItem).toHaveBeenCalledWith("test_corrupt")
        expect(result.is_loading.value).toBe(false)
    })
})
