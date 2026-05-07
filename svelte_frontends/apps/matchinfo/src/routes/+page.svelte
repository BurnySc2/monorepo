<script lang="ts">
import type {
    IGameData,
    IMatchInfo,
    INephestResponse,
    IRunningData,
    ISC2Account,
    ISc2Race,
    ISc2Server,
    ISceneChange,
    ISceneNames,
    IUiData,
} from "@repo/sc2-utils"
import {
    gameResponseRaces,
    getCurrentScene,
    getSceneChange,
    isNephestResponse,
    nephestUrl,
    resetInfo,
    sc2GameUrl,
    sc2UiUrl,
    toNephestRace,
    toNephestServer,
    validateGameFromGameData,
} from "@repo/sc2-utils"
import { Spinner } from "@repo/ui"
import { page } from "$app/state"

const dev = import.meta.env.DEV

let params = $derived({
    twitchUser: page.url.searchParams.get("twitchUser"),
    server: page.url.searchParams.get("server") as ISc2Server | null,
    sc2PollFrequency: parseInt(page.url.searchParams.get("sc2PollFrequency") || "1000", 10),
    maxOpponentMmrDifference: parseInt(page.url.searchParams.get("maxOpponentMmrDifference") || "1000", 10),
})

let info = $state<IMatchInfo>(resetInfo())
let running_data = $state<IRunningData>({ scene: "unknown" })
let sc2_accounts = $state<ISC2Account[]>([])
let running = $state(false)
let loading = $state(true)
let error = $state<string | null>(null)

let poll_interval: ReturnType<typeof setTimeout> | null = null

$effect(() => {
    if (params.twitchUser && params.server && running) {
        pollSc2Api()
    }
    return () => {
        if (poll_interval) {
            clearTimeout(poll_interval)
        }
    }
})

const pollSc2Api = async () => {
    if (!running) {
        return
    }

    poll_interval = setTimeout(() => {
        pollSc2Api()
    }, params.sc2PollFrequency)

    // /game
    try {
        const gameDataResponse = await fetch(sc2GameUrl)
        if (!gameDataResponse.ok) {
            return
        }
        const game_data: IGameData = await gameDataResponse.json()
        let valid_game = validateGameFromGameData(game_data)
        if (valid_game === "other") {
            return
        }

        // /ui
        const uiDataResponse = await fetch(sc2UiUrl)
        if (!uiDataResponse.ok) {
            return
        }
        const ui_data: IUiData = await uiDataResponse.json()
        const current_scene: ISceneNames = getCurrentScene(game_data, ui_data)

        // Find player account
        let my_index = -1
        for (let i = 0; i < sc2_accounts.length; i++) {
            const account = sc2_accounts[i]
            if (account.name === game_data.players[0].name) {
                my_index = 0
                break
            } else if (account.name === game_data.players[1].name) {
                my_index = 1
                break
            }
        }
        if (my_index === -1) {
            return
        }

        const scene_change: ISceneChange = getSceneChange(running_data.scene, current_scene, my_index !== -1)
        if (current_scene === "loading") {
            return
        }
        running_data.scene = current_scene
        if (scene_change !== "toNewGameFromMenu") {
            return
        }

        const opponent_index = 1 - my_index

        if (game_data.players[opponent_index].type === "computer") {
            valid_game = "vsComputer"
        }
        // Clear and set info
        info = resetInfo()
        info = {
            ...info,
            myName: game_data.players[my_index].name,
            myRace: gameResponseRaces[game_data.players[my_index].race] as ISc2Race,
            opponentName: game_data.players[opponent_index].name,
            opponentRace: gameResponseRaces[game_data.players[opponent_index].race] as ISc2Race,
        }
        if (dev) {
            info.opponentName = "Sonic"
            info.opponentRace = "Terran"
        }

        // Get my mmr
        if (info.myName && info.myRace && params.server) {
            await nephestQuery(info.myName, info.myRace, params.server)
            if (
                (valid_game === "1v1" || valid_game === "vsComputer") &&
                info.myMmr !== -1 &&
                info.opponentName &&
                info.opponentRace
            ) {
                await nephestQuery(info.opponentName, info.opponentRace, params.server, info.myMmr)
            }
        }
    } catch (e) {
        error = e instanceof Error ? e.message : "Unknown error"
    }
}

const nephestQuery = async (name: string, race: ISc2Race, server: ISc2Server, myMmr?: number): Promise<boolean> => {
    const url = `${nephestUrl}${name}`
    try {
        const response = await fetch(url)
        if (!response.ok) {
            return false
        }
        const data: unknown = await response.json()

        if (!Array.isArray(data)) {
            return false
        }

        for (const playerAccount of data as INephestResponse[]) {
            const nephestRace = toNephestRace[race]
            if (!playerAccount.members[nephestRace as keyof typeof playerAccount.members]) {
                continue
            }
            if (playerAccount.members.character.region !== toNephestServer[server]) {
                continue
            }

            const accountName = playerAccount.members.character.name.split("#")[0]
            if (accountName !== name) {
                continue
            }

            const currentSeasonGames = playerAccount.currentStats.gamesPlayed
            const currentSeasonMmr = playerAccount.currentStats.rating
            if (currentSeasonGames === null) {
                continue
            }

            // Set streamer info
            if (myMmr === undefined) {
                info.myMmr = currentSeasonMmr
                info._gamesPlayedThisSeason = currentSeasonGames
                return true
            }
            // Set opponent info
            const mmrDiff = Math.abs(currentSeasonMmr - myMmr)
            if (mmrDiff > params.maxOpponentMmrDifference) {
                continue
            }
            if (
                info._opponentGamesPlayedThisSeason !== -1 &&
                currentSeasonGames <= info._opponentGamesPlayedThisSeason
            ) {
                continue
            }

            info.opponentMmr = currentSeasonMmr
            info._opponentGamesPlayedThisSeason = currentSeasonGames
            return true
        }
    } catch (e) {
        console.error("Nephest query failed:", e)
    }
    return false
}

// Initialize on mount
$effect(() => {
    const init = async () => {
        // In production, this would fetch from backend
        // For now, using mock data for development
        sc2_accounts = []
        loading = false
        running = true
    }
    init()

    return () => {
        running = false
    }
})
</script>

<div class="container mx-auto max-w-4xl">
    {#if loading}
        <div class="flex justify-center items-center h-64"><Spinner /></div>
    {:else if error}
        <div class="bg-red-900/50 border border-red-500 rounded-lg p-4 text-red-200">
            <p class="font-semibold">Error</p>
            <p>{error}</p>
        </div>
    {:else}
        <div class="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h1 class="text-2xl font-bold mb-6 text-center">Match Info</h1>

            {#if info.myName}
                <div class="grid grid-cols-2 gap-8">
                    <!-- My Info -->
                    <div class="bg-gray-700 rounded-lg p-4">
                        <h2 class="text-lg font-semibold mb-3 text-green-400">You</h2>
                        <div class="space-y-2">
                            <p><span class="text-gray-400">Name:</span> {info.myName}</p>
                            <p><span class="text-gray-400">Race:</span> {info.myRace || "-"}</p>
                            <p><span class="text-gray-400">MMR:</span> {info.myMmr !== -1 ? info.myMmr : "-"}</p>
                            <p>
                                <span class="text-gray-400">Games:</span>
                                {info._gamesPlayedThisSeason !== -1 ? info._gamesPlayedThisSeason : "-"}
                            </p>
                        </div>
                    </div>

                    <!-- Opponent Info -->
                    <div class="bg-gray-700 rounded-lg p-4">
                        <h2 class="text-lg font-semibold mb-3 text-red-400">Opponent</h2>
                        <div class="space-y-2">
                            <p><span class="text-gray-400">Name:</span> {info.opponentName || "-"}</p>
                            <p><span class="text-gray-400">Race:</span> {info.opponentRace || "-"}</p>
                            <p>
                                <span class="text-gray-400">MMR:</span>
                                {info.opponentMmr !== -1 ? info.opponentMmr : "-"}
                            </p>
                            <p>
                                <span class="text-gray-400">Games:</span>
                                {info._opponentGamesPlayedThisSeason !== -1 ? info._opponentGamesPlayedThisSeason : "-"}
                            </p>
                        </div>
                    </div>
                </div>
            {:else}
                <p class="text-center text-gray-400">Waiting for game data...</p>
            {/if}

            <!-- Scene indicator -->
            <div class="mt-6 pt-4 border-t border-gray-600">
                <p class="text-center text-sm text-gray-500">
                    Scene: <span class="text-white">{running_data.scene}</span>
                </p>
            </div>
        </div>
    {/if}
</div>
