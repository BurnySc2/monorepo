import type { ZodType } from "zod"

export interface PersistedState<T> {
    state: T
    is_loading: { value: boolean }
    reset: () => void
}

export function create_persisted_state<T>(key: string, schema: ZodType<T>, initial: T): PersistedState<T> {
    const browser_initial = typeof window !== "undefined" && typeof localStorage !== "undefined"
    let resolved_initial: T
    if (browser_initial) {
        try {
            const raw = localStorage.getItem(key)
            if (raw !== null) {
                try {
                    resolved_initial = schema.parse(JSON.parse(raw)) as T
                } catch {
                    localStorage.removeItem(key)
                    resolved_initial = schema.parse(initial) as T
                }
            } else {
                resolved_initial = schema.parse(initial) as T
            }
        } catch {
            resolved_initial = schema.parse(initial) as T
        }
    } else {
        resolved_initial = schema.parse(initial) as T
    }
    const state = $state(resolved_initial) as T
    const is_loading = $state({ value: !browser_initial })

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
        const fresh = schema.parse(initial) as T
        apply_value(fresh)
    }

    $effect.root(() => {
        $effect(() => {
            const browser = typeof window !== "undefined" && typeof localStorage !== "undefined"
            if (browser) {
                if (is_loading.value) {
                    is_loading.value = false
                    const data = localStorage.getItem(key)
                    if (data !== null) {
                        try {
                            const parsed = schema.parse(JSON.parse(data)) as T
                            apply_value(parsed)
                        } catch {
                            localStorage.removeItem(key)
                        }
                    }
                } else {
                    localStorage.setItem(key, JSON.stringify(state))
                }
            }

            $state.snapshot(state)
        })
    })

    return { state, is_loading, reset }
}
