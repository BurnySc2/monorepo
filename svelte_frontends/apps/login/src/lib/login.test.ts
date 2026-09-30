import { get_api_base } from "@repo/api-client"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { check_login_status, handle_logout, start_github_login, start_twitch_login } from "./login"

const original_fetch = globalThis.fetch

function create_mock_location() {
    return {
        href: "",
        assign: vi.fn(),
        replace: vi.fn(),
        reload: vi.fn(),
        protocol: "",
        host: "",
        hostname: "",
        port: "",
        pathname: "",
        search: "",
        hash: "",
        state: null,
        scrollX: 0,
        scrollY: 0,
        ancestorOrigins: "",
        open: vi.fn(),
        close: vi.fn(),
        showModal: vi.fn(),
        showOpenFilePicker: vi.fn(),
        showSaveFilePicker: vi.fn(),
        toString: () => "",
    }
}

function create_mock_window() {
    const location = create_mock_location()
    return {
        location,
        fetch: global.fetch,
        console,
    }
}

beforeEach(() => {
    vi.stubEnv("VITE_API_TARGET", "localhost:8000")
    vi.clearAllMocks()
})

afterEach(() => {
    globalThis.fetch = original_fetch
    vi.clearAllMocks()
    vi.unstubAllEnvs()
    vi.restoreAllMocks()
})

describe("check_login_status", () => {
    it("returns logged in state when user is authenticated", async () => {
        const mockUser = { id: 1, name: "testuser", service: "twitch" }
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            statusText: "OK",
            json: () => Promise.resolve({ logged_in: true, user: mockUser }),
        }) as unknown as typeof fetch

        const result = await check_login_status()

        expect(result.is_loading).toBe(false)
        expect(result.is_logged_in).toBe(true)
        expect(result.logged_in_user).toEqual({ id: 1, name: "testuser", service: "twitch" })
        expect(result.error_message).toBeNull()
    })

    it("returns not logged in when user is not authenticated", async () => {
        global.fetch = vi.fn().mockResolvedValue({
            ok: true,
            statusText: "OK",
            json: () => Promise.resolve({ logged_in: false }),
        }) as unknown as typeof fetch

        const result = await check_login_status()

        expect(result.is_loading).toBe(false)
        expect(result.is_logged_in).toBe(false)
        expect(result.logged_in_user).toBeNull()
        expect(result.error_message).toBeNull()
    })

    it("sets error message when fetch fails", async () => {
        global.fetch = vi.fn().mockRejectedValue(new Error("Network error"))

        const result = await check_login_status()

        expect(result.is_loading).toBe(false)
        expect(result.is_logged_in).toBe(false)
        expect(result.error_message).toBe("Failed to connect to server")
    })
})

describe("start_twitch_login", () => {
    it("redirects to twitch login URL", () => {
        const location = create_mock_location()
        const mockWindow = create_mock_window()
        mockWindow.location = location
        vi.stubGlobal("window", mockWindow)

        start_twitch_login()

        expect(location.href).toBe(`${get_api_base()}/login/twitch/start`)
    })
})

describe("start_github_login", () => {
    it("redirects to github login URL", () => {
        const location = create_mock_location()
        const mockWindow = create_mock_window()
        mockWindow.location = location
        vi.stubGlobal("window", mockWindow)

        start_github_login()

        expect(location.href).toBe(`${get_api_base()}/login/github/start`)
    })
})

describe("handle_logout", () => {
    it("reloads page when logout redirects", async () => {
        const reloadSpy = vi.fn()
        const location = create_mock_location()
        location.reload = reloadSpy
        const mockWindow = create_mock_window()
        mockWindow.location = location
        vi.stubGlobal("window", mockWindow)

        global.fetch = vi.fn().mockResolvedValue({
            type: "opaque",
            status: 0,
        }) as unknown as typeof fetch

        await handle_logout()

        expect(reloadSpy).toHaveBeenCalled()
    })

    it("throws error when logout fails", async () => {
        global.fetch = vi.fn().mockRejectedValue(new Error("Network error"))

        await expect(handle_logout()).rejects.toThrow("Logout failed")
    })
})
