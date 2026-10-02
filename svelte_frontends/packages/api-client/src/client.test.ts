import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { ApiError, api_fetch, get_api_error_status } from "./client.js"

const original_fetch = globalThis.fetch
const mock_fetch = vi.fn()

const json_headers = { "Content-Type": "application/json" }
const json_body = JSON.stringify({ text: "hello" })

describe("api_fetch", () => {
    beforeEach(() => {
        vi.stubEnv("VITE_API_TARGET", "localhost:8000")
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.clearAllMocks()
        vi.unstubAllEnvs()
    })

    it.each([
        {
            name: "builds full URL from base and path",
            path: "/login",
            init: undefined,
            expected_url: "http://localhost:8000/login",
            expected_options: {},
        },
        {
            name: "merges credentials include by default",
            path: "/login",
            init: undefined,
            expected_url: "http://localhost:8000/login",
            expected_options: { credentials: "include" },
        },
        {
            name: "preserves explicit credentials override",
            path: "/login",
            init: { credentials: "omit" },
            expected_url: "http://localhost:8000/login",
            expected_options: { credentials: "omit" },
        },
        {
            name: "preserves method",
            path: "/logout",
            init: { method: "POST" },
            expected_url: "http://localhost:8000/logout",
            expected_options: { method: "POST", credentials: "include" },
        },
        {
            name: "preserves headers",
            path: "/tts-generate/generate",
            init: { method: "POST", headers: json_headers },
            expected_url: "http://localhost:8000/tts-generate/generate",
            expected_options: { headers: json_headers },
        },
        {
            name: "preserves body",
            path: "/tts-generate/generate",
            init: { method: "POST", body: json_body },
            expected_url: "http://localhost:8000/tts-generate/generate",
            expected_options: { body: json_body },
        },
    ])("pass-through $name", async ({ path, init, expected_url, expected_options }) => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        await api_fetch(path, init as RequestInit | undefined)
        expect(mock_fetch).toHaveBeenCalledWith(expected_url, expect.objectContaining(expected_options))
    })

    it("throws on !ok with status and path in message", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: false, status: 500, statusText: "Server Error" } as Response)
        mock_fetch.mockResolvedValueOnce({ ok: false, status: 500, statusText: "Server Error" } as Response)
        await expect(api_fetch("/login")).rejects.toThrow("500")
        await expect(api_fetch("/login")).rejects.toThrow("/login")
    })

    it("includes statusText in error message", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: false, status: 404, statusText: "Not Found" } as Response)
        await expect(api_fetch("/missing")).rejects.toThrow("Not Found")
    })

    it("exposes numeric status on error via ApiError", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: false, status: 409, statusText: "Conflict" } as Response)
        const error = await api_fetch("/api/audiobook/upload").catch((e: unknown) => e)
        expect(error).toBeInstanceOf(ApiError)
        expect(error).toBeInstanceOf(Error)
        expect((error as ApiError).status).toBe(409)
        expect((error as ApiError).statusText).toBe("Conflict")
        expect((error as Error).message).toContain("Request failed /api/audiobook/upload: 409")
        expect(get_api_error_status(error)).toBe(409)
    })

    it("get_api_error_status returns undefined for generic errors", () => {
        expect(get_api_error_status(new Error("boom"))).toBeUndefined()
        expect(get_api_error_status(null)).toBeUndefined()
    })

    it("returns response on ok", async () => {
        const response = { ok: true, status: 200, statusText: "OK", json: async () => ({}) } as Response
        mock_fetch.mockResolvedValueOnce(response)
        const result = await api_fetch("/login")
        expect(result).toBe(response)
    })

    it("propagates fetch rejection", async () => {
        mock_fetch.mockRejectedValueOnce(new Error("Network error"))
        await expect(api_fetch("/login")).rejects.toThrow("Network error")
    })
})
