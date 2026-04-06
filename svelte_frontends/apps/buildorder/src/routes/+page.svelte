<script lang="ts">
import type {
    IBuildOrderDbRow,
    IBuildOrderItem,
    IGameData,
    IMatchInfo,
    IRunningData,
    ISC2Account,
    ISc2Race,
    ISc2Server,
    ISceneChange,
    ISceneNames,
    IUiData,
} from "@repo/sc2-utils"
import {
    formatTime,
    gameResponseRaces,
    getCurrentScene,
    getSceneChange,
    resetInfo,
    sc2GameUrl,
    sc2UiUrl,
    validateGameFromGameData,
} from "@repo/sc2-utils"
import { Spinner } from "@repo/ui"
import { page } from "$app/state"

const dev = import.meta.env.DEV

let params = $derived({
    twitchUser: page.url.searchParams.get("twitchUser"),
    server: page.url.searchParams.get("server") as ISc2Server | null,
    sc2PollFrequency: parseInt(page.url.searchParams.get("sc2PollFrequency") || "1000", 10),
})

let buildOrderTitle = $state("Current Build Order Title")
let currentItem = $state<IBuildOrderItem>({ time: 85, text: "Supply Depot" })
let nextItem = $state<IBuildOrderItem>({ time: 105, text: "Barracks" })

let sc2Accounts = $state<ISC2Account[]>([])
let info = $state<IMatchInfo>(resetInfo())
let runningData = $state<IRunningData>({ scene: "unknown" })
let buildOrders = $state<IBuildOrderDbRow[]>([])
let activeBuildOrder = $state<IBuildOrderItem[] | null>(null)
let running = $state(false)
let loading = $state(true)
let endOfBuildOrderReached = $state(true)
let gameTime = $state(0)

let pollInterval: ReturnType<typeof setTimeout> | null = null

$effect(() => {
    if (params.twitchUser && params.server && running) {
        pollSc2Api()
    }
    return () => {
        if (pollInterval) {
            clearTimeout(pollInterval)
        }
    }
})

const pollSc2Api = async () => {
    if (!running) {
        return
    }

    pollInterval = setTimeout(() => {
        pollSc2Api()
    }, params.sc2PollFrequency)

    try {
        // /game
        const gameDataResponse = await fetch(sc2GameUrl)
        if (!gameDataResponse.ok) {
            return
        }
        const gameData: IGameData = await gameDataResponse.json()
        let validGame = validateGameFromGameData(gameData)
        if (validGame === "other") {
            return
        }

        gameTime = gameData.displayTime

        // /ui
        const uiDataResponse = await fetch(sc2UiUrl)
        if (!uiDataResponse.ok) {
            return
        }
        const uiData: IUiData = await uiDataResponse.json()
        const currentScene: ISceneNames = getCurrentScene(gameData, uiData)

        // Find player account
        let myIndex = -1
        for (let i = 0; i < sc2Accounts.length; i++) {
            const account = sc2Accounts[i]
            if (account.name === gameData.players[0].name) {
                myIndex = 0
                break
            } else if (account.name === gameData.players[1].name) {
                myIndex = 1
                break
            }
        }
        if (myIndex === -1) {
            return
        }

        const sceneChange: ISceneChange = getSceneChange(runningData.scene, currentScene, myIndex !== -1)
        if (currentScene === "loading") {
            return
        }
        runningData.scene = currentScene

        if (sceneChange === "toNewGameFromMenu") {
            const opponentIndex = 1 - myIndex

            if (gameData.players[opponentIndex].type === "computer") {
                validGame = "vsComputer"
            }
            // Clear and set info
            info = resetInfo()
            info = {
                ...info,
                myName: gameData.players[myIndex].name,
                myRace: gameResponseRaces[gameData.players[myIndex].race] as ISc2Race,
                opponentName: gameData.players[opponentIndex].name,
                opponentRace: gameResponseRaces[gameData.players[opponentIndex].race] as ISc2Race,
            }
            if (dev) {
                info.opponentName = "Sonic"
                info.opponentRace = "Terran"
            }
            // Get matchup, then get first build order matching matchup
            if (activeBuildOrder === null && info.myRace && info.opponentRace) {
                const matchup = `${info.myRace[0]}v${info.opponentRace[0]}`
                const buildOrder = buildOrders.find((item) => item.matchup === matchup)
                if (buildOrder) {
                    buildOrderTitle = buildOrder.title
                    activeBuildOrder = buildOrder.buildOrder
                    endOfBuildOrderReached = false
                }
            }
        }

        // Update current/next items based on game time
        if (activeBuildOrder && !endOfBuildOrderReached) {
            let currentIdx = -1
            for (let i = 0; i < activeBuildOrder.length; i++) {
                if (activeBuildOrder[i].time <= gameTime) {
                    currentIdx = i
                } else {
                    break
                }
            }

            if (currentIdx >= activeBuildOrder.length - 1) {
                endOfBuildOrderReached = true
            } else {
                currentItem = activeBuildOrder[currentIdx >= 0 ? currentIdx : 0]
                nextItem = activeBuildOrder[currentIdx + 1]
            }
        }
    } catch (e) {
        console.error("Poll failed:", e)
    }
}

// Initialize on mount
$effect(() => {
    const init = async () => {
        // In production, this would fetch from backend
        // For now, using mock build order data for development
        buildOrders = [
            {
                id: 1,
                enabled: true,
                priority: 1,
                matchup: "TvT",
                title: "Standard Terran vs Terran",
                buildOrder: [
                    { time: 85, text: "Supply Depot" },
                    { time: 105, text: "Barracks" },
                    { time: 130, text: "Refinery" },
                    { time: 155, text: "Orbital Command" },
                    { time: 200, text: "Factory" },
                    { time: 250, text: "Starport" },
                ],
            },
        ]
        sc2Accounts = []
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
    {:else}
        <div class="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h1 class="text-2xl font-bold mb-2 text-center">{buildOrderTitle}</h1>
            <p class="text-center text-gray-400 mb-6">{info.myRace || "?"} vs {info.opponentRace || "?"}</p>

            <!-- Current time -->
            <div class="text-center mb-8">
                <span class="text-5xl font-mono font-bold text-yellow-400"> {formatTime(gameTime)} </span>
            </div>

            {#if endOfBuildOrderReached}
                <div class="text-center py-8">
                    <p class="text-2xl text-gray-400">Build order complete!</p>
                </div>
            {:else if activeBuildOrder}
                <div class="grid grid-cols-2 gap-8">
                    <!-- Current item -->
                    <div class="bg-green-900/50 border-2 border-green-500 rounded-xl p-6">
                        <h2 class="text-sm uppercase tracking-wider text-green-400 mb-2">Current</h2>
                        <p class="text-3xl font-bold mb-2">{currentItem.text}</p>
                        <p class="text-xl text-gray-400">{formatTime(currentItem.time)}</p>
                    </div>

                    <!-- Next item -->
                    <div class="bg-gray-700 rounded-xl p-6">
                        <h2 class="text-sm uppercase tracking-wider text-gray-400 mb-2">Next</h2>
                        <p class="text-3xl font-bold mb-2">{nextItem.text}</p>
                        <p class="text-xl text-gray-400">{formatTime(nextItem.time)}</p>
                    </div>
                </div>
            {:else}
                <p class="text-center text-gray-400">Waiting for matchup data...</p>
            {/if}

            <!-- Scene indicator -->
            <div class="mt-6 pt-4 border-t border-gray-600">
                <p class="text-center text-sm text-gray-500">
                    Scene: <span class="text-white">{runningData.scene}</span>
                </p>
            </div>
        </div>
    {/if}
</div>
