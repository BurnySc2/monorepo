import { afterEach, describe, expect, it, vi } from "vitest"
import { get_api_base, is_local_host } from "./base"

describe("get_api_base", () => {
    afterEach(() => {
        vi.unstubAllEnvs()
    })

    it("returns default when VITE_API_TARGET is undefined", () => {
        vi.stubEnv("VITE_API_TARGET", "")
        expect(get_api_base()).toBe("http://localhost:8000")
    })

    it("uses http for localhost target", () => {
        vi.stubEnv("VITE_API_TARGET", "localhost:8000")
        expect(get_api_base()).toBe("http://localhost:8000")
    })

    it("uses http for localhost with custom port", () => {
        vi.stubEnv("VITE_API_TARGET", "localhost:3000")
        expect(get_api_base()).toBe("http://localhost:3000")
    })

    it("uses https for mylocalhost target (exact hostname match)", () => {
        vi.stubEnv("VITE_API_TARGET", "mylocalhost:8000")
        expect(get_api_base()).toBe("https://mylocalhost:8000")
    })

    it("uses http for localhost subdomain target", () => {
        vi.stubEnv("VITE_API_TARGET", "api.localhost:8000")
        expect(get_api_base()).toBe("http://api.localhost:8000")
    })

    it("uses https for non-localhost host", () => {
        vi.stubEnv("VITE_API_TARGET", "api.example.com")
        expect(get_api_base()).toBe("https://api.example.com")
    })

    it("uses https for non-localhost host with port", () => {
        vi.stubEnv("VITE_API_TARGET", "api.example.com:443")
        expect(get_api_base()).toBe("https://api.example.com:443")
    })

    it("uses http for 127.0.0.1 loopback", () => {
        vi.stubEnv("VITE_API_TARGET", "127.0.0.1:8000")
        expect(get_api_base()).toBe("http://127.0.0.1:8000")
    })

    it("strips http scheme prefix and trailing slash for localhost", () => {
        vi.stubEnv("VITE_API_TARGET", "http://localhost:8000/")
        expect(get_api_base()).toBe("http://localhost:8000")
    })

    it("strips https scheme prefix and trailing slash for remote host", () => {
        vi.stubEnv("VITE_API_TARGET", "https://api.example.com/")
        expect(get_api_base()).toBe("https://api.example.com")
    })

    it("uses http for ::1 loopback", () => {
        vi.stubEnv("VITE_API_TARGET", "::1:8000")
        expect(get_api_base()).toBe("http://::1:8000")
    })

    it("uses http for [::1] loopback with port", () => {
        vi.stubEnv("VITE_API_TARGET", "[::1]:8000")
        expect(get_api_base()).toBe("http://[::1]:8000")
    })
})

describe("is_local_host", () => {
    it("returns true for localhost with and without port", () => {
        expect(is_local_host("localhost:8000")).toBe(true)
        expect(is_local_host("localhost")).toBe(true)
    })

    it("returns true for localhost subdomain and case-insensitive host", () => {
        expect(is_local_host("api.localhost:8000")).toBe(true)
        expect(is_local_host("LOCALHOST:8000")).toBe(true)
    })

    it("returns true for loopback addresses with scheme and brackets", () => {
        expect(is_local_host("127.0.0.1:8000")).toBe(true)
        expect(is_local_host("http://127.0.0.1:8000/")).toBe(true)
        expect(is_local_host("[::1]:8000")).toBe(true)
        expect(is_local_host("::1:8000")).toBe(true)
    })

    it("returns true for https localhost target preserving scheme stripping", () => {
        expect(is_local_host("https://localhost:8000/api")).toBe(true)
    })

    it("returns false for non-local hosts and empty target", () => {
        expect(is_local_host("api.example.com")).toBe(false)
        expect(is_local_host("mylocalhost:8000")).toBe(false)
        expect(is_local_host("")).toBe(false)
    })
})
