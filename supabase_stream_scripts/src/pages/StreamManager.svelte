<script lang="ts">
    import { toast } from "@zerodevx/svelte-toast"
    import { onMount } from "svelte"

    import {
        errorTheme,
        formatTime,
        races,
        sc2AccountsDb,
        sc2BuildOrdersDb,
        servers,
        successTheme,
        supabase,
        textToBuildOrder,
    } from "../functions/constants"
    import { IBuildOrderItem } from "../functions/interfaces"

    // CONSTANTS
    const dev = (process.env.DEV && process.env.DEV === "true") || false
    let matchups = []
    races.forEach((race1) => {
        races.forEach((race2) => {
            matchups.push(`${race1[0]}v${race2[0]}`)
        })
    })
    // END OF CONSTANTS

    // DUMMY VALUES
    let activeAccounts = [
        { id: 1, enabled: true, name: "Pinopino", race: "Turtle terran", server: "Europe" },
        { id: 2, enabled: false, name: "saixy", race: "Zerg", server: "Europe" },
    ]
    let buildOrders = [
        {
            id: 1,
            enabled: true,
            priority: 1,
            matchup: "TvZ",
            title: "Standard bio",
            buildOrder: [
                { time: 14, text: "Supply depot" },
                { time: 41, text: "Barracks" },
            ],
        },
        { id: 2, enabled: false, priority: 1, matchup: "TvP", title: "Uthermal tank push", buildOrder: [] },
    ]
    // END OF DUMMY VALUES

    let twitchUser: string = null

    let activeServerSelected = servers[0]

    $: matchInfoOverlayLink = `${location.origin}?twitchUser=${twitchUser}&server=${activeServerSelected}&sc2PollFrequency=1000&maxOpponentMmrDifference=1000#/matchinfo`
    $: buildOrderOverlayLink = `${location.origin}?twitchUser=${twitchUser}&server=${activeServerSelected}&sc2PollFrequency=1000#/buildorder`

    let buildOrderAnnounceInChatAfterVoting = "Yes"
    let buildOrderVotingTimeDuration = 30

    let matchHistoryDisplayAmount = 5
    let matchHistoryMinimumElapsedTimeToCountAsGame = 30

    let addAccountEnabled = true
    let addAccountUsername = "BuRny"
    let addAccountRace = races[1]
    let addAccountServer = "Europe"

    let addBuildOrderEnabled = true
    let addBuildOrderPriority = 1
    let addBuildOrderTitle = "Standard bio"
    let addBuildOrderText = "0:17 Depot\n0:40 Barracks\n0:47 Gas"
    let addBuildOrderMatchup = matchups[0]

    let sceneSwitcherEnabled = true
    let sceneSwitcherGameScene = "SC2GameScene"
    let sceneSwitcherMenuScene = "SC2MenuScene"
    let sceneSwitcherReplayScene = "SC2ReplayScene"

    let categoryClass = "border-2 border-black p-1 m-1 w-full"
    let inputClass = "border-2 border-black px-1 my-1"

    let sleep = async (milliseconds) => {
        return new Promise((resolve) => setTimeout(resolve, milliseconds))
    }

    onMount(async () => {
        if (dev) {
            twitchUser = process.env.LOCALUSER || "LOCALDEV"
        }
        loadTwitchUserFromSession()
        loadSc2Accounts()
        loadBuildOrders()
    })

    let loadTwitchUserFromSession = async () => {
        for (let i = 0; i < 20; i++) {
            // Doesnt seem to be available on page load
            let session = supabase.auth.session()
            if (session) {
                if (session.user.user_metadata.nickname) {
                    twitchUser = session.user.user_metadata.nickname // case sensitive
                    // twichEmail = session.user.email
                    // twichId = session.user.id
                    // twichAccessToken = session.access_token
                }
                break
            }
            await sleep(100)
        }
    }

    let logInTwitch = async () => {
        await supabase.auth.signIn(
            {
                provider: "twitch",
            },
            {
                redirectTo: `${location.origin}#/streammanager`,
            }
        )
    }
    let logOutTwitch = async () => {
        twitchUser = null
        await supabase.auth.signOut()
    }

    let loadSc2Accounts = async () => {
        const { data, error } = await supabase
            .from(sc2AccountsDb)
            .select()
            .match({ twitchname: twitchUser })
            .order("id")
        if (error !== null) {
            console.log(error)
            return
        }
        console.log(data)
        activeAccounts = []
        data.forEach((row) => {
            activeAccounts.push({
                id: row.id,
                enabled: row.enabled,
                name: row.name,
                race: row.race,
                server: row.server,
            })
        })
    }

    let addSc2Account = async () => {
        const { data, error } = await supabase.from(sc2AccountsDb).insert(
            {
                twitchname: twitchUser,
                enabled: addAccountEnabled,
                name: addAccountUsername,
                race: addAccountRace,
                server: addAccountServer,
            },
            { returning: "minimal" }
        )
        if (error !== null) {
            console.log(error)
            toast.push(`Error adding SC2 Account:<br>${addAccountUsername}`, errorTheme)
            return
        }
        console.log(data)
        toast.push(`Added SC2 Account successfully:<br>${addAccountUsername}`, successTheme)
        addAccountUsername = ""
        await loadSc2Accounts()
    }

    let deleteSc2Account = async (id, accountName) => {
        await supabase.from(sc2AccountsDb).delete().match({ id: id })
        toast.push(`Deleted SC2 Account successfully:<br>${accountName}`, successTheme)
        await loadSc2Accounts()
    }

    let enableDisableSc2Account = async (id: number, enable: boolean) => {
        await supabase.from(sc2AccountsDb).update({ enabled: enable }).match({ id: id })
    }

    let addBuildOrder = async () => {
        const { data, error } = await supabase.from(sc2BuildOrdersDb).insert(
            {
                twitchname: twitchUser,
                enabled: addBuildOrderEnabled,
                priority: addBuildOrderPriority,
                title: addBuildOrderTitle,
                matchup: addBuildOrderMatchup,
                buildOrder: textToBuildOrder(addBuildOrderText),
            },
            { returning: "minimal" }
        )
        if (error !== null) {
            console.log(error)
            toast.push(`Error adding build order:<br>${addBuildOrderTitle}`, errorTheme)
            return
        }
        console.log(data)
        toast.push(`Added build order successfully:<br>${addBuildOrderTitle}`, successTheme)
        addBuildOrderTitle = ""
        addBuildOrderText = ""
        // Toast notification: added build order "title"
        await loadBuildOrders()
    }
    let loadBuildOrders = async () => {
        const { data, error } = await supabase
            .from(sc2BuildOrdersDb)
            .select()
            .match({ twitchname: twitchUser })
            .order("priority", { ascending: false })
            .order("id")
        if (error !== null) {
            console.log(error)
            return
        }
        console.log(data)
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
    let deleteBuildOrder = async (id, buildOrderTitle) => {
        await supabase.from(sc2BuildOrdersDb).delete().match({ id: id })
        toast.push(`Deleted Build order successfully:<br>${buildOrderTitle}`, successTheme)
        await loadBuildOrders()
    }

    let enableDisableBuildOrder = async (id: number, enable: boolean) => {
        await supabase.from(sc2BuildOrdersDb).update({ enabled: enable }).match({ id: id })
    }

    let buildOrderFromJsonToTextArea = (buildOrder: IBuildOrderItem[]): string => {
        // Converts a JSON of build order items to a readable string which can be put into a TextArea
        let mappedItems = buildOrder.map((buildOrderItem) => {
            return `${formatTime(buildOrderItem.time)} ${buildOrderItem.text}`
        })
        return mappedItems.join("\n")
    }
</script>

<div class="flex justify-center">
    <div class="max-w-2xl flex flex-col">
        <div class={`${categoryClass} flex flex-col text-center`}>
            {#if twitchUser !== null}
                <div>You are logged in as {twitchUser}</div>
                <button on:click={logOutTwitch}>Log out of twitch</button>
            {:else}
                <div>You are not logged in</div>
                <button class="border-2 border-black p-2" on:click={logInTwitch}>Log in with twitch</button>
            {/if}
        </div>

        {#if twitchUser !== null}
            <div class={categoryClass}>
                <!--    GENERATE OVERLAY LINKS-->
                <button class="border-2 border-black p-2 hover:bg-blue-300">Generate new overlay links</button>
                <div>
                    <div>Your match info overlay link</div>
                    <textarea bind:value={matchInfoOverlayLink} readonly />
                </div>
                <div>
                    <div>Your build order overlay link</div>
                    <textarea bind:value={buildOrderOverlayLink} readonly />
                </div>
            </div>

            <div class={categoryClass}>
                <div>SC2 Settings</div>
                <div class="flex">
                    <div>Active server</div>
                    <select bind:value={activeServerSelected}>
                        {#each servers as server}
                            <option value={server}>
                                {server}
                            </option>
                        {/each}
                    </select>
                </div>
            </div>

            <div class={categoryClass}>
                <div>Build order settings</div>
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

            <div class={categoryClass}>
                <div>Match history settings</div>
                <div class="flex">
                    <div>Amount of most recent matches to display</div>
                    <input type="number" min="0" max="30" bind:value={matchHistoryDisplayAmount} />
                </div>
                <div class="flex">
                    <div>Minimum time (seconds) elapsed to count as a game</div>
                    <input type="number" min="0" max="30" bind:value={matchHistoryMinimumElapsedTimeToCountAsGame} />
                </div>
            </div>

            <div class={categoryClass}>
                <div>SC2 Accounts</div>
                <div class="grid grid-cols-5">
                    <div>Enabled</div>
                    <div>Name</div>
                    <div>Race</div>
                    <div>Server</div>
                    <div />
                    <input type="checkbox" bind:checked={addAccountEnabled} />
                    <input data-testid="addAccountUsername" bind:value={addAccountUsername} placeholder="Username" />
                    <select bind:value={addAccountRace}>
                        {#each races as race}
                            <option value={race}>
                                {race}
                            </option>
                        {/each}
                    </select>
                    <select bind:value={addAccountServer}>
                        {#each servers as server}
                            <option value={server}>
                                {server}
                            </option>
                        {/each}
                    </select>
                    <button
                        data-testid="addSc2Account"
                        class="border-2 border-black p-1 m-1 hover:bg-green-500"
                        on:click={addSc2Account}>Add</button
                    >
                    {#each activeAccounts as account}
                        <input
                            type="checkbox"
                            bind:checked={account.enabled}
                            on:click={() => {
                                enableDisableSc2Account(account.id, !account.enabled)
                            }}
                        />
                        <div>{account.name}</div>
                        <div>{account.race}</div>
                        <div>{account.server}</div>
                        <button
                            class="border-2 border-black p-1 m-1 hover:bg-red-500"
                            on:click={() => {
                                deleteSc2Account(account.id, account.name)
                            }}>Delete</button
                        >
                    {/each}
                </div>
            </div>

            <div class={categoryClass}>
                <div>SC2 Build orders</div>
                <div class="grid grid-cols-8">
                    <div>Enabled</div>
                    <div>Priority</div>
                    <div>Matchup</div>
                    <div>Title</div>
                    <div>Build Order</div>
                    <div />
                    <div />
                    <div />
                    <input type="checkbox" bind:checked={addBuildOrderEnabled} />
                    <input type="number" bind:value={addBuildOrderPriority} />
                    <select bind:value={addBuildOrderMatchup}>
                        {#each matchups as matchup}
                            <option value={matchup}>
                                {matchup}
                            </option>
                        {/each}
                    </select>
                    <input bind:value={addBuildOrderTitle} />
                    <textarea class="border-2 border-black w-full col-span-3" bind:value={addBuildOrderText} />
                    <!-- Add new build order button -->
                    <button class="border-2 border-black p-1 m-1 hover:bg-green-500" on:click={addBuildOrder}
                        >Add</button
                    >
                    {#each buildOrders as buildOrder}
                        <input
                            type="checkbox"
                            bind:checked={buildOrder.enabled}
                            on:click={() => {
                                enableDisableBuildOrder(buildOrder.id, !buildOrder.enabled)
                            }}
                        />
                        <div>{buildOrder.priority}</div>
                        <div>{buildOrder.matchup}</div>
                        <div>{buildOrder.title}</div>
                        <textarea class="col-span-3">{buildOrderFromJsonToTextArea(buildOrder.buildOrder)}</textarea>
                        <!-- Delete build order button -->
                        <button
                            class="border-2 border-black p-1 m-1 hover:bg-red-500"
                            on:click={() => {
                                deleteBuildOrder(buildOrder.id, buildOrder.title)
                            }}>Delete</button
                        >
                    {/each}
                </div>
            </div>
        {/if}

        {#if dev}
            <div class={categoryClass}>
                <div class="flex">
                    <input type="checkbox" bind:checked={sceneSwitcherEnabled} />
                    <div>Enabled</div>
                </div>
                <div class="grid grid-cols-2">
                    <div>Game scene</div>
                    <input class={inputClass} bind:value={sceneSwitcherGameScene} />
                    <div>Menu scene</div>
                    <input class={inputClass} bind:value={sceneSwitcherMenuScene} />
                    <div>Replay scene</div>
                    <input class={inputClass} bind:value={sceneSwitcherReplayScene} />
                </div>
            </div>
        {/if}
    </div>
</div>
