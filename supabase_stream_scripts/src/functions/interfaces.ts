export type ISC2Account = {
    id: number
    enabled: boolean
    twitchname: string
    name: string
    race: string
    server: string
}

export type IMatchInfo = {
    myName: string
    myRace: ISc2Race
    myMmr: number
    _gamesPlayedThisSeason: number
    opponentName: string
    opponentRace: ISc2Race
    opponentMmr: number
    opponentStream: string
    _opponentGamesPlayedThisSeason: number
}
export type ISc2RaceFromResponse = "Terr" | "Prot" | "Zerg" | "Random"
export type ISc2Race = "Terran" | "Protoss" | "Zerg" | "Random"
export type ISc2Server = "Europe" | "Americas" | "Asia" | "China"

export type IGameData = {
    isReplay: boolean
    displayTime: number
    players: {
        id: number
        name: string
        type: "user" | "computer"
        race: ISc2RaceFromResponse
        result: "undecided" | "winidk" | "lossidk"
    }[]
}

export type IUiData = {
    activeScreens: string[]
}
export type ISceneNames = "game" | "menu" | "replay" | "loading" | "unknown"
export type ISceneChange =
    | "toNewGameFromMenu"
    | "toNewGameFromReplay"
    | "toObserveGame"
    | "toReplayFromMenu"
    | "toReplayFromGame"
    | "toMenu"
    | "noChange"
    | "unknown"
export type IValidGame = "1v1" | "vsComputer" | "other"

export type IRunningData = {
    scene: ISceneNames
}
export type INephestResponse = {
    currentStats: {
        gamesPlayed: number
        rank: number
        rating: number
    }
    previousStats: {
        gamesPlayed: number
        rank: number
        rating: number
    }
    members: {
        terranGamesPlayed?: number
        protossGamesPlayed?: number
        zergGamesPlayed?: number
        randomGamesPlayed?: number
        account: {
            battleTag: string
            id: number
            partition: "GLOBAL"
        }
        character: {
            accountId: number
            battlenetId: number
            clanId: number
            name: string
            realm: 1 | 2 | 3 | 4
            region: "EU" | "NA idk" // TODO complete regions
        }
        clan: {
            activeMembers: number
            avgLeagueType: 4
            avgRating: number
            games: number
            id: number
            members: number
            name: string
            region: "EU" | "NA idk" // TODO complete regions
            tag: string
        }
    }
}

export type IBuildOrderItem = {
    time: number
    text: string
}

export type IBuildOrderDbRow = {
    id: number
    enabled: boolean
    priority: number
    matchup: string
    title: string
    buildOrder: IBuildOrderItem[]
}
