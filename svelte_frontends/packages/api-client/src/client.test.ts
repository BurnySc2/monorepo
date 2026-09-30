import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { ApiError, api_fetch, get_api_error_status } from "./client"

const original_fetch = globalThis.fetch
const mock_fetch = vi.fn()

describe("api_fetch", () => {
    beforeEach(() => {
        vi.stubEnv("VITE_API_TARGET", "localhost:8000")
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.restoreAllMocks()
        vi.unstubAllEnvs()
    })

    it("builds full URL from base and path", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        await api_fetch("/login")
        expect(mock_fetch).toHaveBeenCalledWith("http://localhost:8000/login", expect.objectContaining({}))
    })

    it("merges credentials include by default", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        await api_fetch("/login")
        expect(mock_fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ credentials: "include" }))
    })

    it("preserves explicit credentials override", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        await api_fetch("/login", { credentials: "omit" })
        expect(mock_fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ credentials: "omit" }))
    })

    it("preserves method", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        await api_fetch("/logout", { method: "POST" })
        expect(mock_fetch).toHaveBeenCalledWith(
            "http://localhost:8000/logout",
            expect.objectContaining({ method: "POST", credentials: "include" }),
        )
    })

    it("preserves headers", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        const headers = { "Content-Type": "application/json" }
        await api_fetch("/tts-generate/generate", { method: "POST", headers })
        expect(mock_fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ headers }))
    })

    it("preserves body", async () => {
        mock_fetch.mockResolvedValueOnce({ ok: true, status: 200, statusText: "OK" } as Response)
        const body = JSON.stringify({ text: "hello" })
        await api_fetch("/tts-generate/generate", { method: "POST", body })
        expect(mock_fetch).toHaveBeenCalledWith(expect.any(String), expect.objectContaining({ body }))
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
