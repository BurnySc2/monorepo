export function parse_poll_frequency(raw: string | null): number {
    const parsed = parseInt(raw ?? "1000", 10)
    if (!Number.isFinite(parsed)) {
        return 1000
    }
    return Math.max(250, parsed)
}

export type LoadingState = {
    is_loading: boolean
}

export function create_loading_state(is_loading = false): LoadingState {
    return { is_loading }
}
