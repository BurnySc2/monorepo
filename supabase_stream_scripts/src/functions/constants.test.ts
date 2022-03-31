import { expect, test } from "@jest/globals"
import fc from "fast-check"

import { getCurrentScene, getSceneChange } from "./constants"
import { ISceneChange, ISceneNames } from "./interfaces"

test("get current scene - game", () => {
    const gameData = { isReplay: false, displayTime: 5, players: [] }
    const uiData = { activeScreens: [] }
    expect(getCurrentScene(gameData, uiData)).toBe("game")
})

test("get current scene - replay", () => {
    const gameData = { isReplay: true, displayTime: 5, players: [] }
    const uiData = { activeScreens: [] }
    expect(getCurrentScene(gameData, uiData)).toBe("replay")
})

test("get current scene - loading", () => {
    const gameData = { isReplay: true, displayTime: 5, players: [] }
    const uiData = { activeScreens: ["ScreenLoading/ScreenLoading"] }
    expect(getCurrentScene(gameData, uiData)).toBe("loading")
})
test("get current scene - menu", () => {
    const gameData = { isReplay: true, displayTime: 5, players: [] }
    const uiData = { activeScreens: ["some data"] }
    expect(getCurrentScene(gameData, uiData)).toBe("menu")
})

test("get scene change - no change", () => {
    const sceneValues: ISceneNames[] = ["game", "menu", "unknown", "replay", "loading"]

    fc.assert(
        fc.property(fc.constantFrom(...sceneValues), fc.constantFrom(...sceneValues), (oldScene, newScene) => {
            if (oldScene === newScene) {
                expect(getSceneChange(oldScene, newScene, false)).toBe("noChange")
                expect(getSceneChange(oldScene, newScene, true)).toBe("noChange")
            }
        })
    )
})

test("get scene change - with change", () => {
    const sceneValues: ISceneNames[] = ["game", "menu", "unknown", "replay", "loading"]
    // Pick a value, twice, via "constantFrom"

    fc.assert(
        fc.property(
            fc.constantFrom(...sceneValues),
            fc.constantFrom(...sceneValues),
            fc.boolean(),
            (oldScene, newScene, containsPlayer) => {
                if (oldScene === newScene) {
                    return
                }

                if (["menu", "unknown"].includes(oldScene) && newScene === "game") {
                    if (containsPlayer) {
                        expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toNewGameFromMenu")
                    } else {
                        expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toObserveGame")
                    }
                } else if (oldScene === "replay" && newScene === "game") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toNewGameFromReplay")
                } else if (oldScene === "game" && newScene === "replay") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toReplayFromGame")
                } else if (["menu", "unknown"].includes(oldScene) && newScene === "replay") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toReplayFromMenu")
                } else if (["game", "replay", "loading", "unknown"].includes(oldScene) && newScene === "menu") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("toMenu")
                } else if (["menu", "replay", "game", "unknown"].includes(oldScene) && newScene === "loading") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("noChange")
                } else if (oldScene === "loading" && ["menu", "game", "replay"].includes(newScene)) {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("unknown")
                } else if (newScene === "unknown") {
                    expect(getSceneChange(oldScene, newScene, containsPlayer)).toBe("unknown")
                } else {
                    // Not covered cases should fail
                    expect(() => {
                        false
                    }).toBe(true)
                }
            }
        )
    )
})
