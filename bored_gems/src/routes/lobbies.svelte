<script lang="ts">
    import LobbiesRow from "../components/lobby/LobbiesRow.svelte"
    import CreateLobby from "../components/lobby/CreateLobby.svelte"
    import JoinLobbyPopup from "../components/lobby/JoinLobbyPopup.svelte"

    // BEGIN FAKE DATA
    let lobbies = [
        { creator: "Dsl", name: "Dsl's lobby", players: 1, playersMax: 6, password: "asd" },
        { creator: "BuRny", name: "Poggers' lobby", players: 69, playersMax: 69, password: "" },
    ]
    // END FAKE DATA
    let createLobbyShown = false
    let joinLobbyShown = false
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

    const joinLobby = () => {
        if (selectedLobbyIndex < 0) {
            return
        }
        joinLobbyShown = true
    }
</script>

{#if joinLobbyShown}
    <JoinLobbyPopup bind:joinLobbyShown />
{/if}
{#if createLobbyShown}
    <CreateLobby bind:createLobbyShown />
{:else}
    <div class="flex flex-col h-screen justify-center items-center">
        <div class="flex">
            <div class="flex flex-col">
                <div class="flex flex-col min-w-[50vw] min-h-[50vh] border-2 border-black">
                    <div class="border-b-2 border-black text-center text-2xl">
                        {lobbiesShown.length} Lobbies available
                    </div>
                    {#if !lobbiesShown.length}
                        <div class="m-2 text-center">No lobby available. Create one!</div>
                    {:else}
                        <LobbiesRow bind:selectedLobbyIndex {lobbiesShown} />
                    {/if}
                </div>
                <div class="flex justify-center">
                    <button class="border-2 border-black m-1 p-2 hover:bg-yellow-500" on:click={joinLobby}
                        >Join Lobby</button
                    >
                    <button
                        class="border-2 border-black m-1 p-2 hover:bg-green-500"
                        on:click={() => {
                            createLobbyShown = true
                        }}>Create Lobby</button
                    >
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
{/if}
