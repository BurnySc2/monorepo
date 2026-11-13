import type { VoiceInfo } from "@repo/api-types"

export function list_key(voice: VoiceInfo): string {
    return `${voice.engine}|${voice.locale}|${voice.internal_name}`
}

// WHY engine+internal_name: backend resolves voices by engine_internal_name
export function request_key(voice: VoiceInfo): string {
    return `${voice.engine}_${voice.internal_name}`
}
