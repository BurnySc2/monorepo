import type {
    IGameData,
    IMatchInfo,
    INephestResponse,
    ISceneChange,
    ISceneNames,
    IUiData,
    IValidGame,
} from "./types.js"

export * from "./async.js"
export * from "./dates.js"
export * from "./domains.js"

export const reset_info = (): IMatchInfo => {
    return {
        myName: null,
        myRace: null,
        myMmr: -1,
        _gamesPlayedThisSeason: -1,
        opponentName: null,
        opponentRace: null,
        opponentMmr: -1,
        opponentStream: null,
        _opponentGamesPlayedThisSeason: -1,
    }
}

export const validate_game_from_game_data = (gameData: IGameData): IValidGame => {
    if (gameData.players.length !== 2) {
        return "other"
    }
    return "1v1"
}

export const get_current_scene = (gameData: IGameData, uiData: IUiData): ISceneNames => {
    if (uiData.activeScreens.length === 0) {
        if (gameData.isReplay) {
            return "replay"
        }
        return "game"
    } else if (uiData.activeScreens.length === 1 && uiData.activeScreens[0] === "ScreenLoading/ScreenLoading") {
        return "loading"
    } else if (uiData.activeScreens.length !== 0) {
        return "menu"
    }
    return "unknown"
}

export const get_scene_change = (
    oldScene: ISceneNames,
    newScene: ISceneNames,
    containsPlayer: boolean,
): ISceneChange => {
    if (oldScene === newScene) {
        return "noChange"
    }
    if (newScene === "game") {
        if (["menu", "unknown"].includes(oldScene)) {
            if (containsPlayer) {
                return "toNewGameFromMenu"
            } else {
                return "toObserveGame"
            }
        }
        if (oldScene === "replay") {
            return "toNewGameFromReplay"
        }
        return "unknown"
    }
    if (newScene === "replay") {
        if (["menu", "unknown"].includes(oldScene)) {
            return "toReplayFromMenu"
        }
        if (oldScene === "game") {
            return "toReplayFromGame"
        }
        return "unknown"
    }
    if (newScene === "menu") {
        return "toMenu"
    }
    if (newScene === "loading") {
        return "noChange"
    }
    return "unknown"
}

// Type guard for NephestResponse
export const is_nephest_response = (data: unknown): data is INephestResponse => {
    return typeof data === "object" && data !== null && "currentStats" in data && "members" in data
}
