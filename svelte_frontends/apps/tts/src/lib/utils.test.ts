import { beforeEach, describe, expect, it, vi } from "vitest"
import { build_overlay_url, calculate_reconnect_delay, copy_to_clipboard } from "./utils"

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
})
