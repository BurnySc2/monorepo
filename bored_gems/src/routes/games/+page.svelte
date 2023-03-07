<script lang="ts">
    import { GameStatus, getSearchParamFromUrl, type LobbyInfo } from "../../constants"

    import { onMount } from "svelte"
    import { getSupabaseUserFromSession, supabase, supabaseLobbyTable, supabasePlayerTable } from "../../supabase"
    import type { User } from "@supabase/supabase-js"
    import BeforeGameLobby from "../../components/lobby/BeforeGameLobby.svelte"

    // player (participant of a game lobby) vs observer
    // user (logged-in user) vs guest (logged-out user)

    let lobbyid: string | null = null
    let user: User | null = null
    let lobbyInfo: LobbyInfo | null = null
    let userIsPlayer: boolean = true
    let enteredPassword = ""
    let passwordWasEnteredCorrect = false
    let lobbyIsFull: boolean = true
    let userIsHost: boolean = false

    onMount(async () => {
        // Grab the lobbyid from url
        lobbyid = getSearchParamFromUrl("lobbyid")
        if (!lobbyid) {
            // Lobbyid missing from url params
            return
        }

        // Verify if guest is a user
        user = await getSupabaseUserFromSession()
        if (!user) {
            // Is guest
            return
        }

        // Grab lobby info
        {
            const { data, error } = await supabaseLobbyTable
                .select("id, lobby_host, game_status, player_limit, lobby_name, game_type, lobby_password, created_at")
                .eq("id", lobbyid)
                .single()
            if (error) {
                // TODO lobby doesnt exist
                console.log(error)
                return
            }
            if (!data) {
                return
            }
            console.log(data)
            lobbyInfo = data
            console.log(lobbyInfo)
            console.log(lobbyInfo?.created_at)
            console.log(typeof lobbyInfo?.created_at)

            userIsHost = lobbyInfo!.lobby_host === user.id
        }

        // Verify if user is a player
        {
            // TODO: supabase select on players table to check if lobbyid and user.id has an entry
            const { data, error } = await supabase
                .from("bored_gems_players")
                .select("user")
                .eq("lobby", lobbyid)
                .eq("user", user.id)
                .limit(1)
            if (error) {
                console.log(error)
                return
            }
            if (data.length === 1) {
                userIsPlayer = true
                return
            }
        }

        // Verify lobby is not full, allow users to join
        {
            const { data, error, count } = await supabasePlayerTable
                .select("lobby", { count: "exact" })
                .eq("lobby", lobbyid)
            if (error) {
                // Error counting player
                return
            }
            if (count && lobbyInfo) {
                lobbyIsFull = count >= lobbyInfo.player_limit
            }
        }

        // TODO: If game status === CREATED: another subscription on when the game status has been changed to RUNNING or game lobby was closed

        // TODO: If game status === CREATED: another subscription on when users become players (user joins lobby)

        // TODO: Start websocket handler to register a game move / game action from players
        // const mySubscription = supabase
        //     .from("bored_gems_game_actions")
        //     .on("*", (payload) => {
        //         console.log("Change received!", payload)
        //     })
        //     .subscribe()

        // DONE
    })

    const handleEnteredPassword = async () => {
        if (enteredPassword === "") {
            // TODO: handle error message: please enter a password
            return
        }
        // Query database to check if password matches the lobby password
        const { data, error } = await supabaseLobbyTable
            .select("lobby_name")
            .eq("id", lobbyid)
            .eq("lobby_password", enteredPassword)
            .limit(1)
        enteredPassword = ""
        if (error) {
            // ERROR HANDLING
            return
        }
        if (data.length === 0) {
            // WRONG PASSWORD
            return
        }
        passwordWasEnteredCorrect = true
    }
</script>

{#if !user}
    You are not logged in
{:else if !lobbyInfo}
    Lobby with this id does not exist
{:else if userIsPlayer && lobbyInfo.game_status === GameStatus.CREATED}
    // Render lobby
    <BeforeGameLobby {userIsHost} {lobbyInfo} {user} />
{:else if userIsPlayer}
    <!-- LOBBY EXISTS AND USER IS PLAYER -->
    RENDER GAME, OR LOBBY IF GAME HAS NOT STARTED YET
    <!-- TODO: Render game -->
{:else if lobbyInfo.game_status !== GameStatus.CREATED && !lobbyInfo.allows_observers}
    <!-- LOBBY IS RUNNING OR FINISHED AND DOESNT ALLOW OBSERVERS -->
    Game is already running and does not allow observers
{:else if !lobbyInfo.lobby_password || passwordWasEnteredCorrect}
    <!-- LOBBY IS NOT FULLY AND LOBBYSTATUS===CREATED -->
    <button hidden={lobbyIsFull || lobbyInfo.game_status !== GameStatus.CREATED}>Join as player</button>
    <button hidden={!lobbyInfo?.allows_observers}>Join as observer</button>
    <!-- TODO: Game is created vs game is running vs game is finished -->
{:else if lobbyInfo.lobby_password && !passwordWasEnteredCorrect}
    <!-- LOBBY HAS PASSWORD AND USER IS NOT PLAYER/OBSERVER -->
    <input type="password" bind:value={enteredPassword} />
    <button on:click={handleEnteredPassword}>Join</button>
    <!-- TODO: Game is created vs game is running vs game is finished -->
{:else}
    idk another scenario that i cant think of right meow
{/if}
