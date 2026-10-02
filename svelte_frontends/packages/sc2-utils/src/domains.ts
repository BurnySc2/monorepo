export const BASE_DOMAIN = "burnysc2.xyz"

export const sc2GameUrl = "http://localhost:6119/game"
export const sc2UiUrl = "http://localhost:6119/ui"

export const nephestUrl = "https://www.nephest.com/sc2/api/characters?name="

const envDbAccounts = "sc2accounts"
const envDbBuildOrders = "sc2buildorders"
export const sc2AccountsDb = envDbAccounts
export const sc2BuildOrdersDb = envDbBuildOrders

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
