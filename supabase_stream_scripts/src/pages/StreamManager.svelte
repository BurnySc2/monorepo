<script lang="ts">
    import { onMount } from "svelte"
    import {supabase} from "../functions/constants";

    let races = [
        { id: 1, text: "Protoss"},
        { id: 2, text: "Terran"},
        { id: 3, text: "Zerg"},
        { id: 4, text: "Random"},
    ]
    let servers = [
        { id: 1, text: "Europe"},
        { id: 2, text: "Americas"},
        { id: 3, text: "Asia"},
        { id: 4, text: "Chine"},
    ]

    let matchups = []
    races.forEach((race1, index1) => {
        races.forEach((race2, index2) => {
            matchups.push(
                {
                    id: index1*races.length + index2 + 1,
                    text: `${race1.text[0]}v${race2.text[0]}`,
                }
            )
        })
    })

    // DUMMY VALUES
    let activeAccounts = [
        {enabled: true, name: "Pinopino", race: "Turtle terran", server: "EU",},
        {enabled: false, name: "saixy", race: "Zerg", server: "EU",},
    ]
    let buildOrders = [
        {enabled: true, matchup: "TvZ", title: "Standard bio", text: "blabla1"},
        {enabled: false, matchup: "TvP", title: "Uthermal tank push", text: "blabla2"},
    ]
    // END OF DUMMY VALUES

    let twitchUser = null

    let activeServerSelected = "Europe"

    let buildOrderAnnounceInChatAfterVoting = "Yes"
    let buildOrderVotingTimeDuration = 30

    let matchHistoryDisplayAmount = 5
    let matchHistoryMinimumElapsedTimeToCountAsGame = 30

    let addAccountUsername = "BuRny"
    let addAccountRace = "Terran"
    let addAccountServer = "Europe"

    let addBuildOrderName = "Standard bio"
    let addBuildOrderText = "0:17 Depot\n0:40 Barracks\n0:47 Gas"

    let sceneSwitcherEnabled = true
    let sceneSwitcherGameScene = "SC2GameScene"
    let sceneSwitcherMenuScene = "SC2MenuScene"
    let sceneSwitcherReplayScene = "SC2ReplayScene"

    onMount(async () => {
        const response = await supabase.from("sc2accounts").select("*").order("id")
        if (response.status === 200) {
            console.log(response.data)
            return response.data
        }
    })
</script>


{#if twitchUser !== null}
    <div>
        You are logged in
    </div>
    <button>Log out of twitch</button>
{:else }
    <div>
        You are not logged in
    </div>
    <button class="border-2 border-black p-2">Log in with twitch</button>
{/if}

<div class="border-2 border-black p-1 m-1">
<!--    GENERATE OVERLAY LINKS-->
    <button class="border-2 border-black p-2 hover:bg-blue-300">Generate new overlay links</button>
    <div>
        <div>Your build order voting overlay link</div>
        <textarea readonly>blabla</textarea>
    </div>
</div>

<div class="border-2 border-black p-1 m-1">
    <div>
        SC2 Settings
    </div>
    <div class="flex">
        <div>Active server</div>
        <select bind:value={activeServerSelected} on:change={"() => {}"}>
            {#each servers as server}
                <option value={server}>
                    {server.text}
                </option>
            {/each}
        </select>
    </div>
</div>

<div class="border-2 border-black p-1 m-1">
    <div>
        Build order settings
    </div>
    <div class="flex">
        <div>Voting time duration</div>
        <input type="number" min="0" max="180" bind:value={buildOrderVotingTimeDuration} />
    </div>
    <div class="flex">
        <div>Announce voted build order in chat</div>
        <select bind:value={buildOrderAnnounceInChatAfterVoting}>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
        </select>
    </div>
</div>

<div class="border-2 border-black p-1 m-1">
    <div>
        Match history settings
    </div>
    <div class="flex">
        <div>Amount of most recent matches to display</div>
        <input type="number" min="0" max="30" bind:value={matchHistoryDisplayAmount} />
    </div>
    <div class="flex">
        <div>Minimum time (seconds) elapsed to count as a game</div>
        <input type="number" min="0" max="30" bind:value={matchHistoryMinimumElapsedTimeToCountAsGame} />
    </div>
</div>


<div class="border-2 border-black p-1 m-1">
    <div>SC2 Accounts</div>
    <div class="grid grid-cols-6">
        <div>Enabled</div>
        <div>Name</div>
        <div>Race</div>
        <div>Server</div>
        <div></div>
<!--        TODO add popup: add account popup -->
        <button class="border-2 border-black p-1 m-1 hover:bg-green-500">Add</button>
    {#each activeAccounts as account}
        <input type="checkbox" bind:checked={account.enabled} />
        <div>{account.name}</div>
        <div>{account.race}</div>
        <div>{account.server}</div>
<!--        TODO edit popup: edit account popup -->
        <button class="border-2 border-black p-1 m-1 hover:bg-yellow-500">Edit</button>
<!--        TODO delete popup: confirm delete of account name "blabla"-->
        <button class="border-2 border-black p-1 m-1 hover:bg-red-500">Delete</button>
    {/each}
    </div>
</div>

<div class="border-2 border-black p-1 m-1 flex flex-col">
    <div>Add SC2 Account</div>
    <div class="grid grid-cols-2">
        <div>Username</div>
        <input bind:value={addAccountUsername}/>
        <div>Race</div>
        <select bind:value={addAccountRace} on:change={"() => {}"}>
            {#each races as race}
                <option value={race}>
                    {race.text}
                </option>
            {/each}
        </select>
        <div>Server</div>
        <select bind:value={addAccountServer} on:change={"() => {}"}>
            {#each servers as server}
                <option value={server}>
                    {server.text}
                </option>
            {/each}
        </select>
    </div>
    <button class="self-end border-2 border-black p-1 m-1 hover:bg-green-500">Add SC2 account</button>
</div>


<div class="border-2 border-black p-1 m-1">
    <div>SC2 Build orders</div>
    <div class="grid grid-cols-6">
        <div>Enabled</div>
        <div>Matchup</div>
        <div>Title</div>
        <div>Build Order</div>
        <div></div>
<!--        TODO add popup: add build order popup -->
        <button class="border-2 border-black p-1 m-1 hover:bg-green-500">Add</button>
    {#each buildOrders as buildOrder}
        <input type="checkbox" checked={buildOrder.enabled} />
        <div>{buildOrder.matchup}</div>
        <div>{buildOrder.title}</div>
        <div>{buildOrder.text}</div>
<!--        TODO edit popup: edit build order popup -->
        <button class="border-2 border-black p-1 m-1 hover:bg-yellow-500">Edit</button>
<!--        TODO delete popup: confirm delete of build order popup-->
        <button class="border-2 border-black p-1 m-1 hover:bg-red-500">Delete</button>
    {/each}
    </div>
</div>

<div class="border-2 border-black p-1 m-1 flex flex-col">
    <div>Add/edit build order</div>
    <div class="grid grid-cols-2">
        <div>Matchup</div>
        <select bind:value={addAccountRace} on:change={"() => {}"}>
            {#each matchups as matchup}
                <option value={matchup}>
                    {matchup.text}
                </option>
            {/each}
        </select>
        <div>Name</div>
        <input bind:value={addBuildOrderName}/>
    </div>
    <div>Build Order</div>
    <textarea class="border-2 border-black w-full" bind:value={addBuildOrderText}></textarea>
    <button class="self-end border-2 border-black p-1 m-1 hover:bg-green-500">Add build order</button>
</div>

<div class="border-2 border-black p-1 m-1">
    <div class="flex">
        <input type="checkbox" bind:checked={sceneSwitcherEnabled} />
        <div>Enabled</div>
    </div>
    <div class="grid grid-cols-2">
        <div>Game scene</div>
        <input class="border-2 border-black px-1 my-1" bind:value={sceneSwitcherGameScene} />
        <div>Menu scene</div>
        <input class="border-2 border-black px-1 my-1" bind:value={sceneSwitcherMenuScene} />
        <div>Replay scene</div>
        <input class="border-2 border-black px-1 my-1" bind:value={sceneSwitcherReplayScene} />
    </div>
</div>

