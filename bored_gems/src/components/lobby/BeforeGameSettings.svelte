<script lang="ts">
    import { GameStatus, type LobbyInfo } from "../../constants"

    // svelte-ignore unused-export-let
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

    // TODO: if new settings are different from the settings in the database: show save_settings button
    let settingsHaveChanged = false

    const handleSaveSettings = () => {
        // Settings have been edited and need to be saved in the DB
    }
</script>

<div class="grid grid-cols-2 gap-y-2 mx-2">
    <label for="game">Game type</label>
    <input class="border-2 border-black" id="game" bind:value={lobbyInfo.game_type} />

    <label for="lobbyName">Lobby name</label>
    <input class="border-2 border-black" id="lobbyName" bind:value={lobbyInfo.lobby_name} />

    <!-- TODO: hash and salt and secure lobby passwords -->
    <!-- TODO hint passwords are not encrypted in database! -->
    <label for="password">Lobby password</label>
    <input class="border-2 border-black" id="password" bind:value={lobbyInfo.lobby_password} />

    <label for="maxPlayers">Max players</label>
    <input class="border-2 border-black" id="maxPlayers" type="number" bind:value={lobbyInfo.player_limit} />

    <label for="allowObservers">Allow observers</label>
    <input
        class="border-2 border-black"
        type="checkbox"
        name=""
        id="allowObservers"
        bind:checked={lobbyInfo.allows_observers}
    />
</div>

{#if settingsHaveChanged}
    <!-- Show save changes only if settings have been changed -->
    <button class="border-2 border-black p-2 mx-4 hover:bg-green-500">Save changes</button>
{/if}
