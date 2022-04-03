<script lang="ts">
    import { dev } from "$app/env"
    import { page } from "$app/stores"
    import { onDestroy, onMount } from "svelte"

    import {
        gameResponseRaces,
        getCurrentScene,
        getSceneChange,
        nephestUrl,
        resetInfo,
        sc2AccountsDb,
        sc2GameUrl,
        sc2UiUrl,
        supabase,
        toNephestRace,
        toNephestServer,
        validateGameFromGameData,
    } from "../functions/constants"
    import {
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
        IValidGame,
    } from "../functions/interfaces"

    let sc2Accounts: ISC2Account[] = []
    let params = {
        // http://localhost:3000?twitchUser=BurnySc2&server=Europe&sc2PollFrequency=1&maxOpponentMmrDifference=1000#/matchinfo
        // TODO instead of twitch user get twitch-id
        twitchUser: $page.url.searchParams.get("twitchUser"),
        server: $page.url.searchParams.get("server") as ISc2Server,
        sc2PollFrequency: parseInt($page.url.searchParams.get("sc2PollFrequency")),
        maxOpponentMmrDifference: parseInt($page.url.searchParams.get("maxOpponentMmrDifference")),
    }
    let info: IMatchInfo = resetInfo()
    let runningData: IRunningData = {
        scene: "unknown",
    }

    let running = false
    onMount(async () => {
        await getMyAccounts()
        running = true
        pollSc2Api()
    })
    onDestroy(() => {
        running = false
    })
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
        if (sceneChange !== "toNewGameFromMenu") {
            // No new game has been started, don't change anything
            return
        }
        if (sceneChange === "toMenu") {
            // TODO Hide overlay?
            return
        }
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
        // Get my mmr
        await nephestQuery(info.myName, info.myRace, params.server)
        if ((validGame === "1v1" || validGame === "vsComputer") && info.myMmr !== -1) {
            // Get opponent mmr
            await nephestQuery(info.opponentName, info.opponentRace, params.server, info.myMmr)
            await getOpponentStream()
        }
    }
    let nephestQuery = async (name: string, race: ISc2Race, server: ISc2Server, myMmr?: number): Promise<boolean> => {
        // myMmr not given if query is meant for streamer account, else for opponent account
        let url = `${nephestUrl}${name}`
        // console.log(url)
        let response = await fetch(url)
        if (!response.ok) {
            return false
        }
        let data: INephestResponse[] = await response.json()
        // Match my account by: most games played
        // Match opponent account by: mmr difference < 1000 and pick most games played
        console.log("Checking for", name, race, server, myMmr)
        for (const playerAccount of data) {
            let nephestRace = toNephestRace[race]
            if (playerAccount.members[nephestRace] === undefined) {
                // Race does not match
                continue
            }
            if (playerAccount.members.character.region !== toNephestServer[server]) {
                // Server does not match
                continue
            }
            let accountName = playerAccount.members.character.name.split("#")[0]
            if (accountName !== name) {
                // Accountname does not match
                continue
            }
            // Gather all information
            let currentSeasonGames = playerAccount.currentStats.gamesPlayed
            let currentSeasonMmr = playerAccount.currentStats.rating
            if (currentSeasonGames === null) {
                // This account has no games played this season
                continue
            }
            // Set streamer info
            if (
                myMmr === undefined &&
                (info._gamesPlayedThisSeason === -1 || currentSeasonGames > info._gamesPlayedThisSeason)
            ) {
                info._gamesPlayedThisSeason = currentSeasonGames
                info.myMmr = currentSeasonMmr
            }
            // Set opponent info
            else if (
                myMmr !== undefined &&
                Math.abs(currentSeasonMmr - myMmr) < params.maxOpponentMmrDifference &&
                (info._opponentGamesPlayedThisSeason === -1 || currentSeasonGames > info._opponentGamesPlayedThisSeason)
            ) {
                info._opponentGamesPlayedThisSeason = currentSeasonGames
                info.opponentMmr = currentSeasonMmr
            }
        }
        return true
    }
    let getOpponentStream = async () => {
        const { data } = await supabase
            .from(sc2AccountsDb)
            .select()
            .match({ name: info.opponentName, race: info.opponentRace, server: params.server })
            .limit(1)
            .order("id")
        if (data && data.length !== 0) {
            // TODO Make backend script that updates if a stream is live
            const response = await supabase
                .from("streamonline")
                .select()
                .match({ twitchname: data[0].twitchname })
                .limit(1)
                .order("id")
            let streamData = response.data
            if (streamData && streamData.length !== 0 && streamData[0].live) {
                info.opponentStream = `twitch.tv/${data[0].twitchname}`
            }
        }
    }
</script>

{#if runningData.scene === "game" || dev}
    <div class="rounded-lg bg-blue-800 text-white px-4 py-2 flex flex-col truncate">
        <div class="border-b pb-1 text-xl font-bold">SC2 Info</div>
        <div class="grid grid-cols-1 pt-1">
            {#if info.myMmr !== -1}
                <div>I am at <b>{info.myMmr}mmr</b></div>
            {/if}
            <div>My opponent is <b>{info.opponentName}</b></div>
            {#if info.opponentMmr !== -1}
                <div>They are <b>{info.opponentRace}</b> and at <b>{info.opponentMmr}mmr</b></div>
                {#if info.opponentStream}
                    <div>And stream at <b>{info.opponentStream}</b></div>
                {/if}
            {:else}
                <div>They are <b>{info.opponentRace}</b></div>
            {/if}
            <div>We are playing on <b>{params.server}</b></div>
        </div>
    </div>
{/if}
