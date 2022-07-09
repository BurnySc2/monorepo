export enum GameStatus {
    CREATED = "0",
    RUNNING = "1",
    COMPLETED = "2",
    UNKNOWN = "9",
    // CANCELLED? / Aborted
}

export const getSearchParamFromUrl = (paramToGet: string): any => {
    // From current url, get a searchparams
    const url = new URL(location.href)
    return url.searchParams.get(paramToGet)
}

export type LobbyInfo = {
    id: string
    lobby_host: string // UUID of the game host
    game_status: GameStatus
    player_limit: number
    lobby_name: string
    game_type: string
    lobby_password: string
    created_at: string
    allows_observers: boolean
}

export type PlayerInfo = {
    name: string
    // player_color
}
