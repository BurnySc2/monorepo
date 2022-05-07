<script lang="ts">
    export let createLobbyShown = true

    let newLobby = {
        game: "",
        lobbyName: "",
        password: "",
        maxPlayers: 2,
    }

    const createLobby = () => {
        console.log("creating lobby")
        createLobbyShown = false
    }
</script>

<div class="flex items-center justify-center w-screen h-screen">
    <div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black space-y-2">
        <div class="text-center underline text-2xl py-2">Create new lobby</div>
        <div class="grid grid-cols-2 gap-y-2 mx-2">
            <label for="game">Game</label>
            <input class="border-2 border-black" id="game" bind:value={newLobby.game} />
            <label for="lobbyName">Lobby name</label>
            <input class="border-2 border-black" id="lobbyName" bind:value={newLobby.lobbyName} />
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
            <button class="border-2 border-black p-2 mx-4 hover:bg-green-500" on:click={createLobby}
                >Create lobby</button
            >
        </div>
    </div>
</div>
