import { beforeAll, describe, expect, jest, test } from "@jest/globals"
import { fireEvent, getByTestId, queryByAttribute, render, screen, waitFor } from "@testing-library/svelte"
import { onMount, tick } from "svelte"
import { SvelteComponentDev } from "svelte/internal"

import StreamManager from "./StreamManager.svelte"

describe("Render stream manager", () => {
    const log = console.log

    beforeAll(() => {
        // Supress log output
        console.log = jest.fn()
    })

    test("No log", () => {
        // TODO: test something that should not log
        expect(console.log).not.toHaveBeenCalled()
    })

    test("Visible elements on page load", async () => {
        render(StreamManager as unknown as typeof SvelteComponentDev)
        const instantAvailableTexts = ["You are not logged in", "Log in with twitch"]
        instantAvailableTexts.forEach((text) => {
            const node = screen.getByText(text)
            expect(node).not.toBeNull()
            expect(node instanceof HTMLDivElement || node instanceof HTMLButtonElement).toBeTruthy()
        })
    })
})

describe("Render stream manager login as LOCALTEST", () => {
    const log = console.log

    beforeAll(() => {
        // Supress log output
        console.log = jest.fn()
    })

    test("Visible elements on page load", async () => {
        process.env = {
            ...process.env,
            DEV: "true",
            LOCALUSER: "LOCALTEST",
            SC2ACCOUNTSDB: "sc2accounts_dev",
            SC2BUILDORDERSDB: "sc2buildorders_dev",
        }
        const { getByText, container } = render(StreamManager as unknown as typeof SvelteComponentDev)
        const instantAvailableTexts = ["You are logged in as LOCALTEST", "Log out of twitch"]
        instantAvailableTexts.forEach((text) => {
            const node = screen.getByText(text)
            expect(node).not.toBeNull()
            expect(node instanceof HTMLDivElement || node instanceof HTMLButtonElement).toBeTruthy()
        })

        // expect(getByText('BuRny')).toBeInTheDocument()

        // // Find element with "data-testid" attribute
        // const addAccountUsernameElement = getByTestId(container, "addAccountUsername")
        // expect(addAccountUsernameElement).not.toBeNull()
        // expect(addAccountUsernameElement).toBeInstanceOf(HTMLInputElement)
        // // await fireEvent.change(addAccountUsernameElement, {target: {value: "MYTESTACCOUNT"}})
        // expect(addAccountUsernameElement.textContent).toBe("BuRny")
        // addAccountUsernameElement.textContent = "MYTESTACCOUNT"
        // await tick()
        // expect(addAccountUsernameElement.textContent).toBe("MYTESTACCOUNT")
        // // expect(screen.queryByText("MYTESTACCOUNT")).toBeInstanceOf(HTMLInputElement)
        // // expect(getByText("MYTESTACCOUNT"))

        // const addSc2AccountElement = getByTestId(container, "addSc2Account")
        // await fireEvent.click(addSc2AccountElement)

        // const afterOnMountAvailableTexts = ["MYTESTACCOUNT"]
        // await waitFor(async () => {
        //     await tick()
        //     afterOnMountAvailableTexts.forEach((text) => {
        //         const node = screen.getByText(text)
        //         expect(node).not.toBeNull()
        //         const possibleInstance = [HTMLDivElement, HTMLButtonElement]
        //         expect(node instanceof HTMLButtonElement).toBeTruthy()
        //     })
        // })

        // await tick()
        // const availableTexts = [
        //     "Stream Manager",
        //     "You are logged in as LOCALDEV",
        //     "Log out of twitch",
        //     "http://localhost:3000?twitchUser=LOCALDEV&server=Europe&sc2PollFrequency=1000&maxOpponentMmrDifference=1000#/matchinfo",
        // TODO Enable when scene switcher works
        //     "Enabled",
        //     "Game scene",
        //     "Menu scene",
        //     "Replay scene",
        //     "SC2GameScene",
        //     "SC2MenuScene",
        //     "SC2ReplayScene",
        // ]
        // availableTexts.forEach(async (text) => {
        //     const node = await screen.queryByText(text)
        //     expect(node).not.toBeNull()
        //     expect(node).toBeInstanceOf(Promise)
        // })

        // const node = screen.queryByText("Stream Manager")
        // expect(node).not.toBeNull()
        // expect(node).toBeInstanceOf(Promise)
    })
})
