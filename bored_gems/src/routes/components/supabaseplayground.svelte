<script lang="ts">
    import type { User } from "@supabase/supabase-js"
    import { onMount } from "svelte"

    import { GameStatus } from "../../constants"
    import {
        closeLobby,
        createLobby,
        exitLobby,
        getSupabaseUserFromSession,
        joinLobby,
        listLobbies,
        listPlayersOfLobby,
        loginUser,
        registerUser,
        supabase,
        supabaseLobbyTable,
    } from "../../supabase"

    const playgroundUrl = "/components/supabaseplayground"

    // Register, Login
    let email = ""
    let username = ""
    let password = ""
    // Create lobby, join lobby
    let lobbyId = ""
    let lobbyName = ""
    let lobbyPassword = ""
    // Component state
    let user: User | null = null
    let errorMessage = ""

    onMount(async () => {
        user = await getSupabaseUserFromSession()
    })
    const resetVariables = () => {
        email = ""
        username = ""
        password = ""
    }
    const registerHandler = async () => {
        console.log("Registering...")
        user = await registerUser(email, username, password, playgroundUrl)
        resetVariables()
    }
    const quickRegisterAsTestuser1 = async () => {
        email = "test1@user.com"
        username = "testuser1"
        password = "imtesting"
        await registerHandler()
    }
    const quickRegisterAsTestuser2 = async () => {
        email = "test2@user.com"
        username = "testuser2"
        password = "imtesting"
        await registerHandler()
    }
    const loginHandler = async () => {
        console.log("Logging in...")
        user = await loginUser({
            email: email,
            password: password,
            redirect: playgroundUrl,
        })
        resetVariables()
    }
    const quickLoginAsTestuser1 = async () => {
        email = "test1@user.com"
        password = "imtesting"
        await loginHandler()
    }
    const quickLoginAsTestuser2 = async () => {
        email = "test2@user.com"
        password = "imtesting"
        await loginHandler()
    }
    const logoutHandler = async () => {
        console.log("Logging out...")
        await supabase.auth.signOut()
        user = null
    }
    const quickCreateLobbyHandler = async () => {
        await createLobby({
            lobbyHost: user!,
            gameType: "tictactoe",
            playerLimit: 2,
            lobbyName: lobbyName,
            lobbyPassword: lobbyPassword,
        })
    }
    const disbandLobbyHandler = async () => {
        // As lobby host, disband lobby with given lobby id
        await closeLobby(lobbyId)
    }
    const listAllOpenLobbiesHandler = async () => {
        // TODO In console list all lobbies and their playernumber and playermax
        let data = await listLobbies()
        console.log(data)
    }
    const listPlayersOfLobbyHandler = async () => {
        // TODO In console list all lobbies and their playernumber and playermax
        let data = await listPlayersOfLobby(lobbyId)
        console.log(data)
    }
    const joinLobbyHandler = async () => {
        // TODO able to enter lobby id in a field, then try to join lobby
        await joinLobby(user!, lobbyId, lobbyPassword)
    }
    const leaveLobbyHandler = async () => {
        // TODO as player, leave a lobby
        await exitLobby(user!, lobbyId)
    }
</script>

<div class="flex flex-col h-screen justify-center items-center gap-y-4">
    <div class="text-2xl underline">A page to try out different queries</div>
    {#if user}
        <div>You are logged in as: {user.email}</div>
        <div class="flex flex-col items-center gap-x-4 border-2 border-black p-2">
            <button class="hover:bg-yellow-500 p-2" on:click={logoutHandler}>Logout</button>
            <button class="hover:bg-red-500 p-2">Remove testuser1 account</button>
            <button class="hover:bg-red-500 p-2">Remove testuser2 account</button>
        </div>
        <div class="flex flex-col border-2 border-black p-2 gap-y-1">
            <button on:click={listAllOpenLobbiesHandler}>Show lobbies</button>
            <input type="text" class="border-2 border-black" placeholder="Lobby name" bind:value={lobbyName} />
            <button on:click={quickCreateLobbyHandler} class="hover:bg-green-500">Quick create lobby</button>
            <input type="text" class="border-2 border-black" placeholder="Lobby id" bind:value={lobbyId} />
            <input type="text" class="border-2 border-black" placeholder="Lobby password" bind:value={lobbyPassword} />
            <button on:click={listPlayersOfLobbyHandler}>Show players</button>
            <button on:click={joinLobbyHandler}>Join lobby</button>
            <button on:click={joinLobbyHandler}>Join lobby (password protected)</button>
            <button on:click={disbandLobbyHandler}>Quit/End lobby as host</button>
            <button on:click={leaveLobbyHandler}>Quit lobby</button>
            <button>join lobby as observer (password protected)</button>
            <button>Start game (as host)</button>
        </div>
        <div class="flex flex-col item-center border-2 border-black p-2 gap-y-1">
            <button>join lobby while game is running as observer</button>
            <button>take a turn at a game</button>
        </div>
    {:else}
        <div>You are not logged in</div>
        <div class="flex flex-col gap-x-4 border-2 border-black p-2">
            <input type="text" placeholder="username" bind:value={username} />
            <input type="email" placeholder="email" bind:value={email} />
            <input type="password" placeholder="password" bind:value={password} />
            <button class="hover:bg-green-500" on:click={registerHandler}>Register</button>
            <button class="hover:bg-green-500" on:click={loginHandler}>Login</button>
        </div>
        <div class="flex gap-x-4 border-2 border-black p-2">
            <button class="hover:bg-green-500" on:click={quickRegisterAsTestuser1}>Quick register as testuser1</button>
            <button class="hover:bg-green-500" on:click={quickRegisterAsTestuser2}>Quick register as testuser2</button>
        </div>
        <div class="flex gap-x-4 border-2 border-black p-2">
            <button class="hover:bg-green-500" on:click={quickLoginAsTestuser1}>Quick login as testuser1</button>
            <button class="hover:bg-green-500" on:click={quickLoginAsTestuser2}>Quick login as testuser2</button>
        </div>
    {/if}
    {#if errorMessage}
        <div class="bg-red-300" p-2>{errorMessage}</div>
    {/if}
</div>
