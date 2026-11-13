import type { VoiceInfo } from "@repo/api-types"
import { describe, expect, it } from "vitest"
import { list_key, request_key } from "./samples_keys"

function make_voice(overrides: Partial<VoiceInfo> = {}): VoiceInfo {
    return {
        engine: "edge",
        internal_name: "en-US-AriaNeural",
        label: "Aria",
        gender: "female",
        locale: "en-US",
        ...overrides,
    }
}

describe("samples_keys", () => {
    it("formats engine and internal name", () => {
        const voice = make_voice()
        expect(request_key(voice)).toBe("edge_en-US-AriaNeural")
        expect(list_key(voice)).toBe("edge|en-US|en-US-AriaNeural")
    })

    it("distinguishes same label with different internal names", () => {
        const first = make_voice({ internal_name: "voice-a", label: "Same" })
        const second = make_voice({ internal_name: "voice-b", label: "Same" })
        expect(request_key(first)).not.toBe(request_key(second))
        expect(list_key(first)).not.toBe(list_key(second))
    })
})
