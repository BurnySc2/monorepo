import { beforeEach, describe, expect, it, vi } from "vitest"
import { fetch_times, fetch_tracks } from "./api_client"

const mock_fetch = vi.fn()

global.fetch = mock_fetch

const mock_tracks_response = [
    { id: 1, name: "Track A" },
    { id: 2, name: "Track B" },
]

const mock_times_response = [
    {
        date: "2024-01-15",
        driver_name: "Driver1",
        car_name: "Car A",
        driving_model: "Model X",
        track_name: "Track A",
        best_time: 95230,
    },
    {
        date: "2024-01-16",
        driver_name: "Driver2",
        car_name: "Car B",
        driving_model: "Model Y",
        track_name: "Track A",
        best_time: 97450,
    },
]

describe("fetch_tracks", () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it("returns tracks on successful response", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mock_tracks_response,
        })

        const result = await fetch_tracks()

        expect(result).toHaveLength(2)
        expect(result[0].name).toBe("Track A")
        expect(result[1].id).toBe(2)
    })

    it("throws error on failed response", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: false,
            statusText: "Not Found",
        })

        await expect(fetch_tracks()).rejects.toThrow("Failed to fetch tracks: Not Found")
    })

    it("calls /api/raceroom/tracks", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_tracks()

        expect(mock_fetch).toHaveBeenCalledWith("/api/raceroom/tracks")
    })
})

describe("fetch_times", () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it("returns times on successful response", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mock_times_response,
        })

        const result = await fetch_times()

        expect(result).toHaveLength(2)
        expect(result[0].driver_name).toBe("Driver1")
        expect(result[0].best_time).toBe(95230)
    })

    it("throws error on failed response", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: false,
            statusText: "Server Error",
        })

        await expect(fetch_times()).rejects.toThrow("Failed to fetch times: Server Error")
    })

    it("calls /api/raceroom/times without params", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times()

        expect(mock_fetch).toHaveBeenCalledWith("/api/raceroom/times")
    })

    it("appends track_id query param when provided", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times(5)

        expect(mock_fetch).toHaveBeenCalledWith("/api/raceroom/times?track_id=5")
    })

    it("appends start_date query param when provided", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times(undefined, "2024-01-01")

        expect(mock_fetch).toHaveBeenCalledWith("/api/raceroom/times?start_date=2024-01-01")
    })

    it("appends end_date query param when provided", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times(undefined, undefined, "2024-12-31")

        expect(mock_fetch).toHaveBeenCalledWith("/api/raceroom/times?end_date=2024-12-31")
    })

    it("combines multiple query params", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times(3, "2024-01-01", "2024-12-31")

        expect(mock_fetch).toHaveBeenCalledWith(
            "/api/raceroom/times?track_id=3&start_date=2024-01-01&end_date=2024-12-31",
        )
    })

    it("throws error when fetch fails completely", async () => {
        mock_fetch.mockRejectedValueOnce(new Error("Network error"))

        await expect(fetch_times()).rejects.toThrow()
    })
})
