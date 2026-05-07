import { beforeEach, describe, expect, it, vi } from "vitest"
import { parse_replay_file } from "./api_client"

const mock_fetch = vi.fn()

global.fetch = mock_fetch

const mock_replay_response = {
    user_id: "test_user",
    size: 1234,
    md5: "abc123def456",
    status: "processed",
    teams: [
        {
            result: "Win",
            players: [
                {
                    clan_tag: "Heroes",
                    name: "TestPlayer",
                    pick_race: "Protoss",
                    play_race: "Protoss",
                    is_human: true,
                    mmr: 1500,
                },
            ],
        },
        {
            result: "Loss",
            players: [
                {
                    clan_tag: "",
                    name: "Opponent",
                    pick_race: "Terran",
                    play_race: "Terran",
                    is_human: true,
                    mmr: 1450,
                },
            ],
        },
    ],
    played_timestamp: 1718451000000,
    game_length_seconds: 720,
    map_name: "Test Map",
    region_short: "us",
    expansion: "LotV",
    game_base_build: 12345,
    game_version: "5.0.14",
    game_type: "1v1",
    is_ladder: true,
    is_private: false,
    resume_from_replay: false,
}

const create_mock_file = (name: string): File => {
    const content = new ArrayBuffer(100)
    return new File([content], name, { type: "application/octet-stream" })
}

describe("parse_replay_file", () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it("returns parsed replay data on successful response", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mock_replay_response,
        })

        const file = create_mock_file("test.SC2Replay")
        const result = await parse_replay_file(file)

        expect(result.md5).toBe("abc123def456")
        expect(result.map_name).toBe("Test Map")
        expect(result.teams).toHaveLength(2)
        expect(result.teams[0].players[0].name).toBe("TestPlayer")
    })

    it("throws error with message from response on error", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({ error: "Invalid replay file" }),
        })

        const file = create_mock_file("invalid.SC2Replay")

        await expect(parse_replay_file(file)).rejects.toThrow("Invalid replay file")
    })

    it("throws generic error when error message is missing", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: false,
            json: async () => ({}),
        })

        const file = create_mock_file("invalid.SC2Replay")

        await expect(parse_replay_file(file)).rejects.toThrow("Failed to parse replay")
    })

    it("sends POST request with file as FormData", async () => {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mock_replay_response,
        })

        const file = create_mock_file("test.SC2Replay")
        await parse_replay_file(file)

        expect(mock_fetch).toHaveBeenCalledWith(
            "http://localhost:8000/api/parse_replay",
            expect.objectContaining({
                method: "POST",
            }),
        )

        const call = mock_fetch.mock.calls[0]
        const options = call[1] as RequestInit
        expect(options.body).toBeInstanceOf(FormData)
    })

    it("throws error when fetch fails completely", async () => {
        mock_fetch.mockRejectedValueOnce(new Error("Network error"))

        const file = create_mock_file("test.SC2Replay")

        await expect(parse_replay_file(file)).rejects.toThrow()
    })
})
