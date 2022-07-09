<script lang="ts">
    import { supabaseLobbyTable, supabasePlayerTable } from "../../supabase"
    import { GameStatus, type LobbyInfo, type PlayerInfo } from "../../constants"
    import BeforeGameSettings from "./BeforeGameSettings.svelte"
    import type { User } from "@supabase/supabase-js"

    export let userIsHost = true
    export let lobbyInfo: LobbyInfo = {
        id: "3",
        lobby_host: "asd uwu id",
        game_status: GameStatus.CREATED,
        player_limit: 2,
        lobby_name: "asd",
        game_type: "asd",
        lobby_password: "",
        created_at: "",
        allows_observers: false,
    }
    export let user: User | null = null
    export let players: PlayerInfo[] = [{ name: "player1" }, { name: "player2" }, { name: "player3" }]

    const handleGameStart = async () => {
        // TODO Button to start game
        // TODO Sanity check: tictactoe can only be started with 2 players!
        await supabaseLobbyTable.update({ game_status: GameStatus.RUNNING }).eq("id", lobbyInfo.id)
    }

    const handleCloseLobby = async () => {
        // TODO Button to close lobby
        // TODO Delete moves for the lobby?
        await supabasePlayerTable.delete().match({ lobby: lobbyInfo.id })
        await supabaseLobbyTable.delete().match({ id: lobbyInfo.id })
        window.location.href = "/lobbies"
    }

    const handleExitLobby = async () => {
        // TODO Button to exit lobby
        if (!user) {
            return
        }
        await supabasePlayerTable.delete().match({ lobby: lobbyInfo.id, user: user.id })
        window.location.href = "/lobbies"
    }
</script>

<div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black space-y-2">
    <div class="text-center underline text-2xl py-2">Game lobby</div>
    {#if userIsHost}
        <BeforeGameSettings {lobbyInfo} />
    {/if}
    <div class="border-2 border-black text-center p-2 m-auto">
        <div class="underline text-2xl">Players</div>
        {#each players as player, index}
            <div class={index === 0 ? "bg-yellow-500" : ""}>{player.name}</div>
        {/each}
    </div>

    <div class="flex justify-center items-end grow pb-2">
        {#if userIsHost}
            <!-- TODO: Disable button for 1-3 seconds when a new players joins the lobby -->
            <!-- Start game as host -->
            <button class="border-2 border-black p-2 mx-4 hover:bg-green-500" on:click={handleGameStart}
                >Start game</button
            >
            <!-- Close lobby as host -->
            <button class="border-2 border-black p-2 mx-4 hover:bg-red-500" on:click={handleCloseLobby}
                >Close lobby</button
            >
        {:else}
            <!-- Exit lobby as player -->
            <button class="border-2 border-black p-2 mx-4 hover:bg-red-500" on:click={handleExitLobby}
                >Exit lobby</button
            >
        {/if}
    </div>
</div>
