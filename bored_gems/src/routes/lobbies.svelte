<script lang="ts">
    let lobbies = [
        { name: "Dsl's lobby", players: 1, playersMax: 6, password: "asd" },
        { name: "Poggers' lobby", players: 69, playersMax: 69, password: "" },
    ]
    let selectedLobbyIndex = -1
    let filters = {
        hidePassword: false,
        hideFull: false,
    }
    let filteredLobbies = (myLobbies: typeof lobbies, myFilters: typeof filters) => {
        let filtered: typeof myLobbies = []
        myLobbies.forEach((lobby) => {
            if (myFilters.hideFull && lobby.players === lobby.playersMax) {
                return
            }
            if (myFilters.hidePassword && lobby.password !== "") {
                return
            }
            filtered.push(lobby)
        })
        return filtered
    }
    $: lobbiesShown = filteredLobbies(lobbies, filters)
</script>

<div class="flex flex-col h-screen justify-center items-center">
    <div class="flex">
        <div class="flex flex-col">
            <div class="flex flex-col min-w-[50vh] min-h-[50vh] border-2 border-black">
                <div class="border-b-2 border-black text-center text-2xl">{lobbiesShown.length} Lobbies</div>
                {#if !lobbiesShown.length}
                    <div class="m-2">No lobby available. Create one!</div>
                {/if}
                {#each lobbiesShown as lobby, index}
                    <button
                        class={`flex justify-between items-center border-b-2 border-black p-1 ${
                            selectedLobbyIndex === index ? "bg-yellow-500" : "hover:bg-blue-300"
                        }`}
                        on:click={() => {
                            selectedLobbyIndex = index
                        }}
                    >
                        <div>
                            {lobby.name}
                        </div>
                        <div class="border border-black m-1 p-1">
                            {lobby.players} / {lobby.playersMax}
                        </div>
                    </button>
                {/each}
            </div>
            <div class="flex justify-center">
                <button class="border-2 border-black m-1 p-2 hover:bg-yellow-500">Join Lobby</button>
                <button class="border-2 border-black m-1 p-2 hover:bg-green-500">Create Lobby</button>
            </div>
        </div>
        <div class="flex flex-col p-1">
            <div class="underline">Lobby Filters</div>
            <div>
                <input
                    id="hidepassword"
                    type="checkbox"
                    bind:checked={filters.hidePassword}
                    on:click={() => (selectedLobbyIndex = -1)}
                />
                <label for="hidepassword">Hide Password</label>
            </div>
            <div>
                <input
                    id="hidefull"
                    type="checkbox"
                    bind:checked={filters.hideFull}
                    on:click={() => (selectedLobbyIndex = -1)}
                />
                <label for="hidefull">Hide Full</label>
            </div>
        </div>
    </div>
</div>
