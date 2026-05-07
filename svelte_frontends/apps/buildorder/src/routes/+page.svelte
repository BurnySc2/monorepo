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

let build_order_title = $state("Current Build Order Title")
let current_item = $state<IBuildOrderItem>({ time: 85, text: "Supply Depot" })
let next_item = $state<IBuildOrderItem>({ time: 105, text: "Barracks" })

let sc2_accounts = $state<ISC2Account[]>([])
let info = $state<IMatchInfo>(resetInfo())
let running_data = $state<IRunningData>({ scene: "unknown" })
let build_orders = $state<IBuildOrderDbRow[]>([])
let active_build_order = $state<IBuildOrderItem[] | null>(null)
let running = $state(false)
let loading = $state(true)
let end_of_build_order_reached = $state(true)
let game_time = $state(0)

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

    try {
        // /game
        const gameDataResponse = await fetch(sc2GameUrl)
        if (!gameDataResponse.ok) {
            return
        }
        const game_data: IGameData = await gameDataResponse.json()
        let valid_game = validateGameFromGameData(game_data)
        if (valid_game === "other") {
            return
        }

        game_time = game_data.displayTime

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

        if (scene_change === "toNewGameFromMenu") {
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
            // Get matchup, then get first build order matching matchup
            if (active_build_order === null && info.myRace && info.opponentRace) {
                const matchup = `${info.myRace[0]}v${info.opponentRace[0]}`
                const build_order = build_orders.find((item) => item.matchup === matchup)
                if (build_order) {
                    build_order_title = build_order.title
                    active_build_order = build_order.buildOrder
                    end_of_build_order_reached = false
                }
            }
        }

        // Update current/next items based on game time
        if (active_build_order && !end_of_build_order_reached) {
            let current_idx = -1
            for (let i = 0; i < active_build_order.length; i++) {
                if (active_build_order[i].time <= game_time) {
                    current_idx = i
                } else {
                    break
                }
            }

            if (current_idx >= active_build_order.length - 1) {
                end_of_build_order_reached = true
            } else {
                current_item = active_build_order[current_idx >= 0 ? current_idx : 0]
                next_item = active_build_order[current_idx + 1]
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
        build_orders = [
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
    {:else}
        <div class="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h1 class="text-2xl font-bold mb-2 text-center">{build_order_title}</h1>
            <p class="text-center text-gray-400 mb-6">{info.myRace || "?"} vs {info.opponentRace || "?"}</p>

            <!-- Current time -->
            <div class="text-center mb-8">
                <span class="text-5xl font-mono font-bold text-yellow-400"> {formatTime(game_time)} </span>
            </div>

            {#if end_of_build_order_reached}
                <div class="text-center py-8">
                    <p class="text-2xl text-gray-400">Build order complete!</p>
                </div>
            {:else if active_build_order}
                <div class="grid grid-cols-2 gap-8">
                    <!-- Current item -->
                    <div class="bg-green-900/50 border-2 border-green-500 rounded-xl p-6">
                        <h2 class="text-sm uppercase tracking-wider text-green-400 mb-2">Current</h2>
                        <p class="text-3xl font-bold mb-2">{current_item.text}</p>
                        <p class="text-xl text-gray-400">{formatTime(current_item.time)}</p>
                    </div>

                    <!-- Next item -->
                    <div class="bg-gray-700 rounded-xl p-6">
                        <h2 class="text-sm uppercase tracking-wider text-gray-400 mb-2">Next</h2>
                        <p class="text-3xl font-bold mb-2">{next_item.text}</p>
                        <p class="text-xl text-gray-400">{formatTime(next_item.time)}</p>
                    </div>
                </div>
            {:else}
                <p class="text-center text-gray-400">Waiting for matchup data...</p>
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
