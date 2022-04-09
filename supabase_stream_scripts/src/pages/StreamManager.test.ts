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
        const { getByText } = render(StreamManager as unknown as typeof SvelteComponentDev)
        const instantAvailableTexts = ["You are logged in as LOCALTEST", "Log out of twitch"]
        instantAvailableTexts.forEach((text) => {
            const node = screen.getByText(text)
            expect(node).not.toBeNull()
            expect(node instanceof HTMLDivElement || node instanceof HTMLButtonElement).toBeTruthy()
        })
    })
})
