import { goto } from "$app/navigation"
import { createClient } from "@supabase/supabase-js"
import type { Session, User } from "@supabase/supabase-js"

import { GameStatus } from "./constants"

const supabaseUrl = "https://xplbweeaklyxixlugeju.supabase.co"
const supabaseAnonKey =
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwbGJ3ZWVha2x5eGl4bHVnZWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUwMzUwMTcsImV4cCI6MTk2MDYxMTAxN30.PPa4MEwdlaSQovk5lyKqIyxsxp7ujYqjlNGMsctho8k"

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
// TODO Make username primary key = unique
// 16:57 CENSORED: cant change to unique when editing, just creating column
export const supabaseUsernameTable = supabase.from("bored_gems_usernames")
/**
- Policy:
Pick username (username not taken, min and max name length, user.id exists in auth users):

Policy for updating accounts: Username change etc TODO
*/

export const supabaseLobbyTable = supabase.from("bored_gems_lobby")
/**
Policy: 
- If lobby.status != CREATED, lobby is not visible for non-players if observers are not allowed
- Allow creating lobbies for all users
- Allow deleting lobby only for lobby host
*/

export const supabasePlayerTable = supabase.from("bored_gems_players")
/**
Policy:
- Allow join if you arent part of the lobby, and lobby isnt full, and lobby is in status==CREATED
- Allow leave if you are part of lobby and status==CREATED

*/

export const getSupabaseUserFromSession = async (): Promise<User | null> => {
    const session: Session | null = await supabase.auth.session()
    if (session) {
        let user: User | null = session.user
        if (user) {
            return user
        }
    }
    return null
}

export const getUsernameOfUser = async (user: User): Promise<string | null> => {
    if (!user.email) {
        return null
    }
    const response = await supabaseUsernameTable.select("username").eq("user_id", user.id).limit(1).single()
    return response.data.username || null
}

export const registerUser = async (
    email: string,
    username: string,
    password: string,
    redirect: string | null
): Promise<User | null> => {
    const { user, error } = await supabase.auth.signUp({
        email: email,
        password: password,
    })
    if (error !== null) {
        throw error
    }
    // Connect username with user account (foreignkey = email)
    // TODO: Change foreign key to user or user.id
    const { error: error2 } = await supabaseUsernameTable.insert([
        {
            username: username,
            user_id: user!.id,
        },
    ])
    if (error2) {
        throw error2
    }
    if (redirect !== null) {
        goto(redirect)
    }
    return user
}

export const loginUser = async (loginInput: {
    email: string
    password: string
    redirect?: string
}): Promise<User | null> => {
    const { user, error } = await supabase.auth.signIn({
        email: loginInput.email,
        password: loginInput.password,
    })
    if (error !== null) {
        throw error
    }
    if (loginInput.redirect !== undefined) {
        goto(loginInput.redirect)
    }
    return user
}

export const createLobby = async (lobbyInput: {
    lobbyHost: User
    gameType: string
    playerLimit: number
    lobbyName: string
    lobbyPassword: string
}): Promise<any> => {
    // Add new lobby to database for people to be able to join
    let hostUserName = await getUsernameOfUser(lobbyInput.lobbyHost)
    if (hostUserName === null) {
        throw "Unable to get username of lobby host"
    }
    let { data, error } = await supabaseLobbyTable
        .insert({
            lobby_host_id: lobbyInput.lobbyHost.id,
            lobby_host_name: hostUserName,
            game_type: lobbyInput.gameType,
            game_status: GameStatus.CREATED,
            player_limit: lobbyInput.playerLimit,
            lobby_name: lobbyInput.lobbyName, // TODO: if lobby name not given, it will not be shown on the gamelobbies page
            lobby_password: lobbyInput.lobbyPassword,
            // TODO: allow spectators? bool
        })
        .single()
    if (error) {
        throw error
    }
    // Add creator as player
    await joinLobby(lobbyInput.lobbyHost, data.id, lobbyInput.lobbyPassword, hostUserName)
    // TODO: Add type
    return data
}

export const startGame = async (lobbyId: string) => {
    // The host is starting the game
    await supabaseLobbyTable.update({ game_status: GameStatus.RUNNING }).eq("id", lobbyId)
}

export const closeLobby = async (lobbyId: string, redirect: string | null = null) => {
    // The host of a lobby closes the lobby, removing all players from the lobby
    await supabasePlayerTable.delete().match({ lobby: lobbyId })
    await supabaseLobbyTable.delete().match({ id: lobbyId })
    if (redirect) {
        goto(redirect)
    }
}

export const joinLobby = async (user: User, lobbyId: string, lobbyPassword: string, username?: string) => {
    // A user is joining a lobby, making him become a player
    let { error: errorInsert } = await supabasePlayerTable.insert({
        lobby_id: lobbyId,
        user_id: user.id,
        entered_password: lobbyPassword,
        username: username,
    })
    if (errorInsert) {
        throw errorInsert
    }
}

export const exitLobby = async (user: User, lobbyId: string, redirect: string | null = null) => {
    // A player is exiting a lobby
    await supabasePlayerTable.delete().match({ lobby: lobbyId, user: user.id })
    if (redirect) {
        goto(redirect)
    }
}

export const listLobbies = async (): Promise<any[] | null> => {
    // List all available lobbies that a user can join
    // - exclude full
    // - exclude running lobbies that disallows observers
    // - show lobbies you have joined (created or running)
    let { data, error } = await supabaseLobbyTable.select("id, lobby_host_name, lobby_name, player_limit")
    if (error) {
        throw error
    }
    return data
}

export const listPlayersOfLobby = async (lobbyId: string) => {
    // Given a lobbyId, list all the players that have joined the lobby
    let { data, error } = await supabasePlayerTable.select("username").match({ lobby_id: lobbyId })
    if (error) {
        throw error
    }
    return data
}
