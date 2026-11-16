export function clamp_volume_percent(raw: unknown): number {
    const parsed = Number(raw)
    if (!Number.isFinite(parsed)) {
        return 100
    }
    const rounded = Math.round(parsed)
    if (rounded < 0) {
        return 0
    }
    if (rounded > 100) {
        return 100
    }
    return rounded
}

export function clamp_volume_ratio(raw: unknown): number {
    return clamp_volume_percent(raw) / 100
}
