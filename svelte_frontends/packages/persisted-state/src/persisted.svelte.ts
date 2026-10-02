import type { ZodType } from "zod"

export interface PersistedState<T> {
    state: T
    is_loading: { value: boolean }
    reset: () => void
}

function is_browser(): boolean {
    return typeof window !== "undefined" && typeof localStorage !== "undefined"
}

function load_stored<T>(key: string, schema: ZodType<T>, initial: T): T {
    const fallback = schema.parse(initial) as T
    if (!is_browser()) {
        return fallback
    }
    try {
        const raw = localStorage.getItem(key)
        if (raw === null) {
            return fallback
        }
        return schema.parse(JSON.parse(raw)) as T
    } catch {
        try {
            localStorage.removeItem(key)
        } catch {
            // WHY ignore cleanup errors: stale key must not block fallback
        }
        return fallback
    }
}

function save_stored(key: string, value: unknown): void {
    try {
        localStorage.setItem(key, JSON.stringify(value))
    } catch {
        // WHY ignore quota errors: memory state stays usable without persistence
    }
}

export function create_persisted_state<T>(key: string, schema: ZodType<T>, initial: T): PersistedState<T> {
    const browser = is_browser()
    const resolved_initial = load_stored(key, schema, initial)
    const state = $state(resolved_initial) as T
    const is_loading = $state({ value: !browser })

    // WHY in-place merge: $state identity must stay stable for subscribers
    function apply_value(value: T): void {
        if (Array.isArray(state) && Array.isArray(value)) {
            const state_array = state as unknown[]
            const value_array = value as unknown[]
            state_array.splice(0, state_array.length, ...value_array)
        } else if (typeof state === "object" && state !== null && typeof value === "object" && value !== null) {
            Object.assign(state as Record<string, unknown>, value as Record<string, unknown>)
        }
    }

    function reset(): void {
        // WHY in-place reset: T is object/array in practice, identity must persist
        const fresh = schema.parse(initial) as T
        apply_value(fresh)
    }

    $effect.root(() => {
        $effect(() => {
            if (browser) {
                if (is_loading.value) {
                    is_loading.value = false
                    apply_value(load_stored(key, schema, initial))
                } else {
                    save_stored(key, state)
                }
            }
            // WHY snapshot tracks reads: subscribes effect to nested state mutations
            $state.snapshot(state)
        })
    })

    return { state, is_loading, reset }
}
