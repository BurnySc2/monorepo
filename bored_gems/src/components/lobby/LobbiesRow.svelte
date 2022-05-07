<script lang="ts">
    export let selectedLobbyIndex = -1
    export let lobbiesShown = [
        { creator: "Dsl", name: "Dsl's lobby", players: 1, playersMax: 6, password: "asd" },
        { creator: "BuRny", name: "Poggers' lobby", players: 69, playersMax: 69, password: "" },
    ]
    const headerClasses = "border-b-2 border-black p-2"
    const rowClasses = "text-center"

    $: getRowClasses = (index: number) => {
        return selectedLobbyIndex === index ? "bg-yellow-500" : "hover:bg-blue-300"
    }
    const setSelectedLobbyIndex = (index: number) => {
        selectedLobbyIndex = index
    }
</script>

<table class="table-auto">
    <thead>
        <tr>
            <th class={headerClasses}>Creator</th>
            <th class={headerClasses}>Lobby name</th>
            <th class={headerClasses}>Players</th>
        </tr>
    </thead>
    <tbody>
        {#each lobbiesShown as lobbyData, index}
            <tr
                class={`${rowClasses} ${getRowClasses(index)}`}
                on:click={() => {
                    setSelectedLobbyIndex(index)
                }}
            >
                <td>
                    {lobbyData.name}
                </td>
                <td>
                    {lobbyData.creator}
                </td>
                <td>
                    {lobbyData.players} / {lobbyData.playersMax}
                </td>
            </tr>
        {/each}
    </tbody>
</table>
