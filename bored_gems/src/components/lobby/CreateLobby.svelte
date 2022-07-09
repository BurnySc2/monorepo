<script lang="ts">
    import { GameStatus } from "../../constants"

    import { getSupabaseUserFromSession, supabase, supabaseLobbyTable, supabasePlayerTable } from "../../supabase"

    export let createLobbyShown = true

    let newLobby = {
        gameType: "", // e.g. tictacoe
        lobbyName: "",
        password: "",
        maxPlayers: 2, // TODO tictactoe is 2 player game, so participant number is always 2
    }

    const handleCreateLobby = async () => {
        console.log("creating lobby")
        const userFromSession = await getSupabaseUserFromSession()
        if (!userFromSession) {
            // TODO: Could not create lobby because logged in user is not available
            // TODO: redirect to login page?
            return
        }
        // Add new lobby to database for people to be able to join
        let { data, error } = await supabaseLobbyTable
            .insert({
                lobby_host: userFromSession.id,
                game_type: newLobby.gameType,
                game_status: GameStatus.CREATED,
                player_limit: newLobby.maxPlayers,
                lobby_name: newLobby.lobbyName, // TODO: if lobby name not given, it will not be shown on the gamelobbies page
                lobby_password: newLobby.password,
                // TODO: allow spectators? bool
            })
            .single()
        if (error) {
            // TODO: error in lobby creation
            return
        }
        console.log(data) // TODO: REMOVE ME

        // Add creator as player
        await supabasePlayerTable.insert({
            lobby: data.id,
            user: userFromSession.id,
        })
        // What does this do? do i need it
        createLobbyShown = false

        // Use lobby id to redirect to game lobby
        window.location.href = `/games?lobbyid=${data.id}`
    }
</script>

<div class="flex items-center justify-center h-screen">
    <div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black space-y-2">
        <div class="text-center underline text-2xl py-2">Create new lobby</div>
        <div class="grid grid-cols-2 gap-y-2 mx-2">
            <label for="game">Game</label>
            <input class="border-2 border-black" id="game" bind:value={newLobby.gameType} />
            <label for="lobbyName">Lobby name</label>
            <input class="border-2 border-black" id="lobbyName" bind:value={newLobby.lobbyName} />
            <!-- TODO: hash and salt and secure lobby passwords -->
            <!-- TODO hint passwords are not encrypted in database! -->
            <label for="password">Lobby password</label>
            <input class="border-2 border-black" id="password" bind:value={newLobby.password} />
            <label for="maxPlayers">Max players</label>
            <input class="border-2 border-black" id="maxPlayers" type="number" bind:value={newLobby.maxPlayers} />
        </div>
        <div class="flex justify-center items-end grow pb-2">
            <button
                class="border-2 border-black p-2 mx-4 hover:bg-red-500"
                on:click={() => {
                    createLobbyShown = false
                }}>Cancel</button
            >
            <button class="border-2 border-black p-2 mx-4 hover:bg-green-500" on:click={handleCreateLobby}
                >Create lobby</button
            >
        </div>
    </div>
</div>
