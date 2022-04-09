<script lang="ts">
    import { page } from "$app/stores"
    import { onDestroy, onMount } from "svelte"

    import {
        formatTime,
        gameResponseRaces,
        getCurrentScene,
        getSceneChange,
        resetInfo,
        sc2AccountsDb,
        sc2BuildOrdersDb,
        sc2GameUrl,
        sc2UiUrl,
        supabase,
        validateGameFromGameData,
    } from "../functions/constants"
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
    } from "../functions/interfaces"

    const dev = (process.env.DEV && process.env.DEV === "true") || false

    let buildOrderTitle = "Current Build Order Title"
    let currentItem: IBuildOrderItem = { time: 85, text: "Supply Depot" }
    let nextItem: IBuildOrderItem = { time: 105, text: "Barracks" }

    let sc2Accounts: ISC2Account[] = []
    let params = {
        // http://localhost:3000?twitchUser=BurnySc2&server=Europe&sc2PollFrequency=1#/buildorder
        // TODO instead of twitch user get twitch-id
        twitchUser: $page.url.searchParams.get("twitchUser"),
        server: $page.url.searchParams.get("server") as ISc2Server,
        sc2PollFrequency: parseInt($page.url.searchParams.get("sc2PollFrequency")),
    }
    let info: IMatchInfo = resetInfo()
    let runningData: IRunningData = {
        scene: "unknown",
    }
    let buildOrders: IBuildOrderDbRow[] = []
    let activeBuildOrder: IBuildOrderItem[] | null = null

    let running = false
    let endOfBuildOrderReached = true

    onMount(async () => {
        await getMyBuildOrders()
        await getMyAccounts()
        running = true
        pollSc2Api()
    })
    onDestroy(() => {
        running = false
    })

    const getMyBuildOrders = async () => {
        // get initial available build orders
        const { data, error } = await supabase
            .from(sc2BuildOrdersDb)
            .select()
            .match({ twitchname: params.twitchUser, enabled: true })
            // Order by priority?
            .order("priorty", { ascending: false })
            .order("id")
        if (error !== null) {
            console.log(error)
            return
        }
        buildOrders = []
        data.forEach((row) => {
            buildOrders.push({
                id: row.id,
                enabled: row.enabled,
                priority: row.priority,
                matchup: row.matchup,
                title: row.title,
                buildOrder: row.buildOrder,
            })
        })
    }
    let getMyAccounts = async () => {
        const { data, error } = await supabase
            .from(sc2AccountsDb)
            .select()
            .match({ twitchname: params.twitchUser, enabled: true, server: params.server })
            .order("id")
        sc2Accounts = []
        data.forEach((row: ISC2Account) => {
            sc2Accounts.push({
                id: row.id,
                enabled: row.enabled,
                twitchname: row.twitchname,
                name: row.name,
                race: row.race,
                server: row.server,
            })
        })
        console.log("Found sc2 accounts belonging to streamer:", sc2Accounts)
    }

    let pollSc2Api = async () => {
        // check if we are in a game, get the ingame time
        if (!running) {
            // Component was unmounted
            return
        }

        setTimeout(() => {
            pollSc2Api()
        }, params.sc2PollFrequency)

        // /game
        let gameDataResponse = await fetch(sc2GameUrl)
        if (!gameDataResponse.ok) {
            // Game url didnt respond
            return
        }
        let gameData: IGameData = await gameDataResponse.json()
        let validGame = validateGameFromGameData(gameData)
        if (validGame === "other") {
            // Not a valid 1v1 game (either vs human or computer)
            return
        }
        // /ui
        let uiDataResponse = await fetch(sc2UiUrl)
        if (!uiDataResponse.ok) {
            // Ui url didnt respond
            return
        }
        let uiData: IUiData = await uiDataResponse.json()
        let currentScene: ISceneNames = getCurrentScene(gameData, uiData)

        // Find player account
        let myIndex = -1
        for (const account of sc2Accounts) {
            if (account.name === gameData.players[0].name) {
                myIndex = 0
                break
            } else if (account.name === gameData.players[1].name) {
                myIndex = 1
                break
            }
        }
        if (myIndex === -1) {
            // Account not found in list of accounts
            return
        }
        let sceneChange: ISceneChange = getSceneChange(runningData.scene, currentScene, myIndex !== -1)
        if (currentScene === "loading") {
            // Do nothing when loading
            return
        }
        runningData.scene = currentScene
        if (sceneChange === "toNewGameFromMenu") {
            // New game has been started, update build order
            let opponentIndex = 1 - myIndex

            if (gameData.players[opponentIndex].type == "computer") {
                validGame = "vsComputer"
            }
            // Clear stats
            info = resetInfo()
            // Get player names and races
            info = {
                ...info,
                ...{
                    myName: gameData.players[myIndex].name,
                    myRace: gameResponseRaces[gameData.players[myIndex].race] as ISc2Race,
                    opponentName: gameData.players[opponentIndex].name,
                    opponentRace: gameResponseRaces[gameData.players[opponentIndex].race] as ISc2Race,
                },
            }
            if (dev) {
                info.opponentName = "Sonic"
                info.opponentRace = "Terran"
            }
            // Get matchup, then get first build order in the list matching matchup
            if (activeBuildOrder === null) {
                let matchup = `${info.myRace[0]}v${info.opponentRace[0]}`
                let buildOrder = buildOrders.find((item) => {
                    return item.matchup === matchup
                })
                if (buildOrder === undefined) {
                    // Unable to find
                    return
                }
                buildOrderTitle = buildOrder.title
                activeBuildOrder = buildOrder.buildOrder
                endOfBuildOrderReached = false
            }
        }

        // If in game and game is active, update build order
        if (sceneChange !== "noChange" && currentScene === "game" && !endOfBuildOrderReached) {
            updateBuildOrder(gameData)
        }
    }

    let updateBuildOrder = (gameData: IGameData) => {
        let currentItem = activeBuildOrder.find((item: IBuildOrderItem) => {
            return item.time > gameData.displayTime
        })
        let currentItemIndex = activeBuildOrder.indexOf(currentItem)
        let nextItem = activeBuildOrder[currentItemIndex + 1]
        if (nextItem === undefined && currentItem.time + 30 > gameData.displayTime) {
            // End of build order reached, next item could not be found
            endOfBuildOrderReached = true
        }
    }
</script>

<div hidden={!endOfBuildOrderReached}>
    <div>{buildOrderTitle}</div>
    <div class="grid grid-cols-2">
        <div>{formatTime(currentItem.time)}</div>
        <div>{currentItem.text}</div>
        <div>{formatTime(nextItem.time)}</div>
        <div>{nextItem.text}</div>
    </div>
</div>
