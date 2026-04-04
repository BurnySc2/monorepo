import type {
    IBuildOrderItem,
    IGameData,
    IMatchInfo,
    INephestResponse,
    ISceneChange,
    ISceneNames,
    IUiData,
    IValidGame,
} from "./types"

// SC2 API URLs (localhost)
export const sc2GameUrl = "http://localhost:6119/game"
export const sc2UiUrl = "http://localhost:6119/ui"

// External API URLs
export const nephestUrl = "https://www.nephest.com/sc2/api/characters?name="
// Database table names
const envDbAccounts = "sc2accounts"
const envDbBuildOrders = "sc2buildorders"
export const sc2AccountsDb = envDbAccounts
export const sc2BuildOrdersDb = envDbBuildOrders

// Race mappings
export const gameResponseRaces: Record<string, string> = {
    Terr: "Terran",
    Prot: "Protoss",
    Zerg: "Zerg",
    random: "Random",
}

export const toNephestRace: Record<string, string> = {
    Terran: "terranGamesPlayed",
    Protoss: "protossGamesPlayed",
    Zerg: "zergGamesPlayed",
    random: "randomGamesPlayed",
}

export const toNephestServer: Record<string, string> = {
    Europe: "EU",
}

export const races = ["Protoss", "Terran", "Zerg", "Random"]
export const servers = ["Europe", "Americas", "Asia", "China"]

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

export const validateGameFromGameData = (gameData: IGameData): IValidGame => {
    if (gameData.players.length !== 2) {
        return "other"
    }
    return "1v1"
}

export const getCurrentScene = (gameData: IGameData, uiData: IUiData): ISceneNames => {
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
        return "noChange"
    }
    return "unknown"
}

export const formatTime = (timeInSeconds: number): string => {
    const minutes = Math.floor(timeInSeconds / 60)
    const seconds = Math.floor(timeInSeconds % 60)
    const minutesString = `${minutes}`
    const secondsString = seconds.toString().padStart(2, "0")
    return `${minutesString}:${secondsString}`
}

export const timeStringToNumber = (timeFormatted: string): number => {
    const timeSplit = timeFormatted.split(":")
    console.assert(timeSplit.length === 2, timeSplit)
    const minutes = parseInt(timeSplit[0], 10)
    const seconds = parseInt(timeSplit[1], 10)
    return minutes * 60 + seconds
}

export const textToBuildOrder = (buildOrderText: string): IBuildOrderItem[] => {
    const lines = buildOrderText.split("\n")
    const buildOrder: IBuildOrderItem[] = []
    lines.forEach((line) => {
        const timeAndText = line.split(" ")
        const time = timeAndText[0]
        const text = timeAndText.slice(1).join(" ")
        buildOrder.push({
            time: timeStringToNumber(time),
            text: text,
        })
    })
    return buildOrder
}

// Type guard for NephestResponse
export const isNephestResponse = (data: unknown): data is INephestResponse => {
    return typeof data === "object" && data !== null && "currentStats" in data && "members" in data
}
