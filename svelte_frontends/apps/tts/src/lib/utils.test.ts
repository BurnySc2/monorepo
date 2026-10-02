import type { VoiceInfo } from "@repo/api-types"
import * as fc from "fast-check"
import { beforeEach, describe, expect, it, vi } from "vitest"
import {
    build_overlay_url,
    calculate_reconnect_delay,
    clamp_voice_index,
    clamp_volume_percent,
    clamp_volume_ratio,
    copy_to_clipboard,
    get_preview_text,
} from "./utils"

const FC_SEED = Number(process.env.FC_SEED ?? 42)

function create_voice(overrides: Partial<VoiceInfo> = {}): VoiceInfo {
    return {
        engine: "edge",
        internal_name: "en-US-AvaNeural",
        label: "Ava",
        gender: "Female",
        locale: "en-US",
        ...overrides,
    }
}

describe("build_overlay_url", () => {
    it("constructs URL with channel and volume", () => {
        const result = build_overlay_url("burnysc2", 15)
        expect(result).toBe("https://burnysc2.xyz/tts-api/twitch/burnysc2?volume=15")
    })

    it("handles different channel names", () => {
        const result = build_overlay_url("testchannel", 50)
        expect(result).toBe("https://burnysc2.xyz/tts-api/twitch/testchannel?volume=50")
    })

    it("handles volume at boundaries", () => {
        expect(build_overlay_url("ch", 0)).toBe("https://burnysc2.xyz/tts-api/twitch/ch?volume=0")
        expect(build_overlay_url("ch", 100)).toBe("https://burnysc2.xyz/tts-api/twitch/ch?volume=100")
    })
})

describe("copy_to_clipboard", () => {
    const mock_clipboard = {
        writeText: vi.fn(),
    }
    Object.defineProperty(navigator, "clipboard", {
        value: mock_clipboard,
        writable: true,
    })

    beforeEach(() => {
        vi.clearAllMocks()
    })

    it("calls navigator.clipboard.writeText with given text", async () => {
        mock_clipboard.writeText.mockResolvedValueOnce(undefined)
        await copy_to_clipboard("test text")
        expect(mock_clipboard.writeText).toHaveBeenCalledWith("test text")
    })

    it("forwards text from overlay URL", async () => {
        mock_clipboard.writeText.mockResolvedValueOnce(undefined)
        const url = build_overlay_url("burnysc2", 15)
        await copy_to_clipboard(url)
        expect(mock_clipboard.writeText).toHaveBeenCalledWith("https://burnysc2.xyz/tts-api/twitch/burnysc2?volume=15")
    })
})

describe("calculate_reconnect_delay", () => {
    it("starts with 1 second delay for first attempt", () => {
        expect(calculate_reconnect_delay(0)).toBe(1000)
    })

    it("doubles delay for each subsequent attempt", () => {
        expect(calculate_reconnect_delay(1)).toBe(2000)
        expect(calculate_reconnect_delay(2)).toBe(4000)
        expect(calculate_reconnect_delay(3)).toBe(8000)
    })

    it("caps delay at 30 seconds", () => {
        expect(calculate_reconnect_delay(10)).toBe(30000)
        expect(calculate_reconnect_delay(15)).toBe(30000)
    })

    it("caps delay at max for high attempt counts", () => {
        expect(calculate_reconnect_delay(4)).toBe(16000)
        expect(calculate_reconnect_delay(5)).toBe(30000)
        expect(calculate_reconnect_delay(10)).toBe(30000)
    })

    it("falls back to 1000 for NaN and negative attempts", () => {
        expect(calculate_reconnect_delay(Number.NaN)).toBe(1000)
        expect(calculate_reconnect_delay(-1)).toBe(1000)
    })

    it("falls back to 1000 for infinite attempts with clamp", () => {
        expect(calculate_reconnect_delay(Number.POSITIVE_INFINITY)).toBe(1000)
        expect(calculate_reconnect_delay(-5)).toBe(1000)
    })
})

describe("volume clamp properties", () => {
    it("clamp_volume_percent stays bounded in 0..100 and is idempotent", () => {
        fc.assert(
            fc.property(fc.double({ noNaN: false }), (volume) => {
                const clamped = clamp_volume_percent(volume)
                expect(clamped).toBeGreaterThanOrEqual(0)
                expect(clamped).toBeLessThanOrEqual(100)
                expect(Number.isInteger(clamped)).toBe(true)
                expect(clamp_volume_percent(clamped)).toBe(clamped)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })

    it("clamp_volume_ratio stays bounded in 0..1 and is idempotent", () => {
        fc.assert(
            fc.property(fc.double({ noNaN: false }), (volume) => {
                const clamped = clamp_volume_ratio(volume)
                expect(clamped).toBeGreaterThanOrEqual(0)
                expect(clamped).toBeLessThanOrEqual(1)
                expect(clamp_volume_ratio(clamped)).toBe(clamped)
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("backoff properties", () => {
    it("reconnect delay is monotonic and capped in 1000..30000", () => {
        fc.assert(
            fc.property(fc.integer({ min: -10, max: 20 }), fc.integer({ min: -10, max: 20 }), (a, b) => {
                const delay_a = calculate_reconnect_delay(a)
                const delay_b = calculate_reconnect_delay(b)
                expect(delay_a).toBeGreaterThanOrEqual(1000)
                expect(delay_a).toBeLessThanOrEqual(30000)
                expect(delay_b).toBeGreaterThanOrEqual(1000)
                expect(delay_b).toBeLessThanOrEqual(30000)
                if (a <= b) {
                    expect(delay_a).toBeLessThanOrEqual(delay_b)
                } else {
                    expect(delay_b).toBeLessThanOrEqual(delay_a)
                }
            }),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("overlay url encode properties", () => {
    it("encode round-trip preserves trimmed channel and clamped volume", () => {
        fc.assert(
            fc.property(
                fc.stringMatching(/^[A-Za-z0-9_ ]{1,20}$/),
                fc.integer({ min: -50, max: 150 }),
                (channel, volume) => {
                    const trimmed = channel.trim()
                    if (trimmed === "") {
                        return
                    }
                    const url = build_overlay_url(channel, volume)
                    const prefix = "https://burnysc2.xyz/tts-api/twitch/"
                    expect(url.startsWith(prefix)).toBe(true)
                    const without_prefix = url.slice(prefix.length)
                    const channel_part = without_prefix.split("?volume=")[0]
                    expect(decodeURIComponent(channel_part)).toBe(trimmed)
                    const volume_part = Number(without_prefix.split("?volume=")[1])
                    expect(volume_part).toBe(clamp_volume_percent(volume))
                },
            ),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})

describe("clamp_voice_index", () => {
    it.each([
        [99, 1, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 0],
        [5, 0, 0],
        [-1, 3, 0],
    ])("clamps index %i with count %i to %i", (index, count, want) => {
        expect(clamp_voice_index(index, count)).toBe(want)
    })

    it("passes through valid index", () => {
        expect(clamp_voice_index(1, 3)).toBe(1)
        expect(clamp_voice_index(2, 3)).toBe(2)
    })

    it("clamps B1 OOB: stored index 99 with single voice to 0", () => {
        expect(clamp_voice_index(99, 1)).toBe(0)
    })
})

describe("get_preview_text", () => {
    it("returns empty string for empty voices without throwing", () => {
        expect(get_preview_text([], 0, "hello")).toBe("")
        expect(get_preview_text([], 99, "hello")).toBe("")
    })

    it("returns empty string for OOB index without throwing (B1)", () => {
        const voices = [create_voice()]
        expect(get_preview_text(voices, 99, "hello")).toBe("")
    })

    it("formats preview for valid selection", () => {
        const voices = [create_voice({ engine: "edge", label: "Ava Voice" })]
        expect(get_preview_text(voices, 0, "hello")).toBe("edge_ava_voice: hello")
    })

    it("load_voices clamp + preview integration: OOB stored index resolves safely", () => {
        const voices = [create_voice()]
        const stored_index = 99
        const clamped = clamp_voice_index(stored_index, voices.length)
        expect(clamped).toBe(0)
        expect(() => get_preview_text(voices, stored_index, "hello")).not.toThrow()
        expect(get_preview_text(voices, stored_index, "hello")).toBe("")
        expect(get_preview_text(voices, clamped, "hello")).toContain("hello")
    })
})

describe("voice selection properties", () => {
    it("clamped index is always in range or zero and preview never throws", () => {
        fc.assert(
            fc.property(
                fc.array(fc.string({ maxLength: 20 }), { maxLength: 5 }),
                fc.integer({ min: -10, max: 20 }),
                fc.string({ maxLength: 50 }),
                (labels, index, user_text) => {
                    const voices = labels.map((label) => create_voice({ label: label || "Voice" }))
                    const clamped = clamp_voice_index(index, voices.length)
                    expect(clamped).toBeGreaterThanOrEqual(0)
                    if (voices.length > 0 && index >= 0 && index < voices.length) {
                        expect(clamped).toBe(index)
                    } else {
                        expect(clamped).toBe(0)
                    }
                    expect(() => get_preview_text(voices, index, user_text)).not.toThrow()
                    const preview = get_preview_text(voices, index, user_text)
                    expect(typeof preview).toBe("string")
                    if (voices.length === 0 || index < 0 || index >= voices.length) {
                        expect(preview).toBe("")
                    }
                },
            ),
            { seed: FC_SEED, numRuns: 100 },
        )
    })
})
