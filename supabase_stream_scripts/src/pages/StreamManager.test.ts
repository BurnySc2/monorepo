import { beforeAll, describe, expect, jest, test } from "@jest/globals"
import { render, screen } from "@testing-library/svelte"

import StreamManager from "./StreamManager.svelte"

describe("Render stream manager", () => {
    beforeAll(() => {
        // Supress log output
        console.log = jest.fn()
    })

    test("No log", () => {
        // TODO: test something that should not log
        expect(console.log).not.toHaveBeenCalled()
    })

    test("Visible elements on page load", async () => {
        render(StreamManager)
        const instantAvailableTexts = ["You are not logged in", "Log in with twitch"]
        instantAvailableTexts.forEach((text) => {
            const node = screen.getByText(text)
            expect(node).not.toBeNull()
            expect(node instanceof HTMLDivElement || node instanceof HTMLButtonElement).toBeTruthy()
        })
    })
})

describe("Render stream manager login as LOCALTEST", () => {
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
        render(StreamManager)
        const instantAvailableTexts = ["You are logged in as LOCALTEST", "Log out of twitch"]
        instantAvailableTexts.forEach((text) => {
            const node = screen.getByText(text)
            expect(node).not.toBeNull()
            expect(node instanceof HTMLDivElement || node instanceof HTMLButtonElement).toBeTruthy()
        })
    })
})
