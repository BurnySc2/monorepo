import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { fetch_times, fetch_tracks } from "./api_client"

const original_fetch = globalThis.fetch
const mock_fetch = vi.fn()

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
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.clearAllMocks()
        vi.unstubAllEnvs()
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

        await expect(fetch_tracks()).rejects.toThrow(/Request failed \/api\/raceroom\/tracks.*Not Found/)
    })

    it("calls /api/raceroom/tracks", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_tracks()

        expect(mock_fetch).toHaveBeenCalledWith(
            "http://localhost:8000/api/raceroom/tracks",
            expect.objectContaining({ credentials: "include" }),
        )
    })
})

describe("fetch_times", () => {
    beforeEach(() => {
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.clearAllMocks()
        vi.unstubAllEnvs()
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

        await expect(fetch_times()).rejects.toThrow(/Request failed \/api\/raceroom\/times.*Server Error/)
    })

    it.each([
        [undefined, undefined, undefined, "http://localhost:8000/api/raceroom/times"],
        [5, undefined, undefined, "http://localhost:8000/api/raceroom/times?track_id=5"],
        [undefined, "2024-01-01", undefined, "http://localhost:8000/api/raceroom/times?start_date=2024-01-01"],
        [undefined, undefined, "2024-12-31", "http://localhost:8000/api/raceroom/times?end_date=2024-12-31"],
        [
            3,
            "2024-01-01",
            "2024-12-31",
            "http://localhost:8000/api/raceroom/times?track_id=3&start_date=2024-01-01&end_date=2024-12-31",
        ],
    ])("builds query track_id=%s start_date=%s end_date=%s -> %s", async (track_id, start_date, end_date, expected_url) => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => [],
        })

        await fetch_times(
            track_id as number | undefined,
            start_date as string | undefined,
            end_date as string | undefined,
        )

        expect(mock_fetch).toHaveBeenCalledWith(expected_url, expect.objectContaining({ credentials: "include" }))
    })

    it("throws error when fetch fails completely", async () => {
        mock_fetch.mockRejectedValueOnce(new Error("Network error"))

        await expect(fetch_times()).rejects.toThrow()
    })
})
