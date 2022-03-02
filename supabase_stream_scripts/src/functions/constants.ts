import { createClient } from "@supabase/supabase-js"

import { IGameData, IMatchInfo, ISceneChange, ISceneNames, IUiData } from "./interfaces"

export const sc2GameUrl = "http://localhost:6119/game"
export const sc2UiUrl = "http://localhost:6119/ui"
export const nephestUrl = "https://www.nephest.com/sc2/api/characters?name="

// Supabase
export const supabase = createClient(
    "https://xplbweeaklyxixlugeju.supabase.co",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhwbGJ3ZWVha2x5eGl4bHVnZWp1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDUwMzUwMTcsImV4cCI6MTk2MDYxMTAxN30.PPa4MEwdlaSQovk5lyKqIyxsxp7ujYqjlNGMsctho8k"
)

export const races = ["Protoss", "Terran", "Zerg", "Random"]
export const servers = ["Europe", "Americas", "Asia", "China"]

export const gameResponseRaces = { Terr: "Terran", Prot: "Protoss", Zerg: "Zerg", random: "Random" }
export const toNephestRace = {
    Terran: "terranGamesPlayed",
    Protoss: "protossGamesPlayed",
    Zerg: "zergGamesPlayed",
    random: "randomGamesPlayed", // TODO check if random is correct
}
export const toNephestServer = {
    Europe: "EU",
    // TODO other servers
}

export const resetInfo = (): IMatchInfo => {
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

export const getCurrentScene = (gameData: IGameData, uiData: IUiData): ISceneNames => {
    // Check changes:
    // Menu => loading: new game event, dont get mmr yet, might be replay
    // loading => game: new game event, get mmr
    // game => menu
    // game => replay
    // menu => replay
    // replay => menu
    if (uiData.activeScreens.length === 0) {
        // Game or replay
        if (gameData.isReplay) {
            return "replay"
        }
        return "game"
    } else if (uiData === { activeScreens: ["ScreenLoading/ScreenLoading"] }) {
        return "loading"
    } else if (uiData.activeScreens.length !== 0) {
        return "menu"
    }
    return "unknown"
}

export const getSceneChange = (oldScene: ISceneNames, newScene: ISceneNames, containsPlayer: boolean): ISceneChange => {
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
        // This may have to be changed
        return "noChange"
    }
    return "unknown"
}
