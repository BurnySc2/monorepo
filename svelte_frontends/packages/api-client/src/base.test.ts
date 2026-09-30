import { afterEach, describe, expect, it, vi } from "vitest"
import { get_api_base, is_local_host } from "./base"

describe("get_api_base", () => {
    afterEach(() => {
        vi.unstubAllEnvs()
    })

    it.each([
        ["returns default when VITE_API_TARGET is undefined", "", "http://localhost:8000"],
        ["uses http for localhost target", "localhost:8000", "http://localhost:8000"],
        ["uses http for localhost with custom port", "localhost:3000", "http://localhost:3000"],
        ["uses https for mylocalhost target (exact hostname match)", "mylocalhost:8000", "https://mylocalhost:8000"],
        ["uses http for localhost subdomain target", "api.localhost:8000", "http://api.localhost:8000"],
        ["uses https for non-localhost host", "api.example.com", "https://api.example.com"],
        ["uses https for non-localhost host with port", "api.example.com:443", "https://api.example.com:443"],
        ["uses http for 127.0.0.1 loopback", "127.0.0.1:8000", "http://127.0.0.1:8000"],
        [
            "strips http scheme prefix and trailing slash for localhost",
            "http://localhost:8000/",
            "http://localhost:8000",
        ],
        [
            "strips https scheme prefix and trailing slash for remote host",
            "https://api.example.com/",
            "https://api.example.com",
        ],
        ["uses http for ::1 loopback", "::1:8000", "http://::1:8000"],
        ["uses http for [::1] loopback with port", "[::1]:8000", "http://[::1]:8000"],
    ])("%s", (_name, target, expected) => {
        vi.stubEnv("VITE_API_TARGET", target)
        expect(get_api_base()).toBe(expected)
    })
})

describe("is_local_host", () => {
    it.each([
        "localhost:8000",
        "localhost",
        "api.localhost:8000",
        "LOCALHOST:8000",
        "127.0.0.1:8000",
        "http://127.0.0.1:8000/",
        "[::1]:8000",
        "::1:8000",
        "https://localhost:8000/api",
    ])("returns true for %s", (target) => {
        expect(is_local_host(target)).toBe(true)
    })

    it.each(["api.example.com", "mylocalhost:8000", ""])("returns false for %s", (target) => {
        expect(is_local_host(target)).toBe(false)
    })
})
