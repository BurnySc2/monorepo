import { expect, test } from "@playwright/test"

test("index page has hello world", async ({ page }) => {
    await page.goto("/")
    expect(await page.innerText("body")).toContain("Hello world!")
    expect(await page.innerText("body")).toContain("Visit the Svelte tutorial to learn how to build Svelte apps.")
})

test("from index page i get to all other pages", async ({ page }) => {
    await page.goto("/")
    await page.click("#about")
    await page.waitForURL("/about")
    expect(await page.innerText("body")).toContain(
        "This is my about page! Here I display features of svelte that I have implemented"
    )
    await page.click("#chat")
    await page.waitForURL("/normalchat")
    expect(await page.innerText("body")).toContain("Connect to chat")
    await page.click("#todo")
    await page.waitForURL("/todo")
    await page.waitForLoadState("networkidle")
    expect(await page.innerText("body")).toContain("Unable to connect to server - running local mode")
    await page.click("#browserstorage")
    await page.waitForURL("/browserstorage")
    expect(await page.innerText("body")).toContain("Local Storage")
    expect(await page.innerText("body")).toContain("Session Storage")
    //     await page.click("#slug")
    //     await page.waitForURL("/todo/hello-world")
    //     expect(await page.innerText("body")).toContain('Hi! You are on page "/todo/hello-world"')
})

test("about page has click me button", async ({ page }) => {
    await page.goto("/about")
    expect(await page.innerText("#mybutton")).toContain("Click me: this text")
    await page.click("#mybutton")
    expect(await page.textContent("#mybutton")).toContain("Click me: is changing")
})

test("chat page has connect to chat button", async ({ page }) => {
    await page.goto("/normalchat")
    expect(await page.innerText("body")).toContain("Connect to chat")
    await page.fill("#username", "test user")
    expect(await page.inputValue("#username")).toBe("test user")
    expect(await page.innerText("body")).not.toContain("WebSocket is not yet ready!")
    await page.click("#connect")
    expect(await page.inputValue("#username")).toBe("test user")
    expect(await page.innerText("body")).toContain("WebSocket is not yet ready!")
})

test("todo page works", async ({ page }) => {
    await page.goto("/todo")
    expect(await page.innerText("body")).toContain("Submit")
    expect(await page.innerText("body")).toContain("SubmitBody")
    expect(await page.innerText("body")).toContain("SubmitModel")
    // Example todo
    expect(await page.innerText("body")).toContain("some todo text")
    // Warning that backend server is not reachable
    await page.waitForLoadState("networkidle")
    expect(await page.innerText("body")).toContain("Unable to connect to server - running local mode")

    // Submit button
    expect(await page.innerText("body")).not.toContain("test todo1")
    expect(await page.inputValue("#newTodoInput")).toBe("")
    await page.fill("#newTodoInput", "test todo1")
    expect(await page.inputValue("#newTodoInput")).toBe("test todo1")
    await page.click("#submit1")
    await page.waitForTimeout(100)
    expect(await page.inputValue("#newTodoInput")).toBe("")
    expect(await page.innerText("body")).toContain("test todo1")

    // SubmitBody button
    expect(await page.innerText("body")).not.toContain("test todo2")
    expect(await page.inputValue("#newTodoInput")).toBe("")
    await page.fill("#newTodoInput", "test todo2")
    expect(await page.inputValue("#newTodoInput")).toBe("test todo2")
    await page.click("#submit2")
    await page.waitForTimeout(100)
    expect(await page.inputValue("#newTodoInput")).toBe("")
    expect(await page.innerText("body")).toContain("test todo2")

    // SubmitModel button
    expect(await page.innerText("body")).not.toContain("test todo3")
    expect(await page.inputValue("#newTodoInput")).toBe("")
    await page.fill("#newTodoInput", "test todo3")
    expect(await page.inputValue("#newTodoInput")).toBe("test todo3")
    await page.click("#submit3")
    await page.waitForTimeout(100)
    expect(await page.inputValue("#newTodoInput")).toBe("")
    expect(await page.innerText("body")).toContain("test todo3")
})

test("browserstorage works as expected", async ({ page }) => {
    await page.goto("/browserstorage")
    expect(await page.innerText("body")).toContain("Local Storage")
    expect(await page.innerText("body")).toContain("Session Storage")
    expect(await page.innerText("#localStorageValue")).toBe("0")
    expect(await page.innerText("#sessionStorageValue")).toBe("0")
})

test(`browserstorage single`, async ({ page }) => {
    const amountIncrease = 5
    const amountDecrease = 7

    await page.goto("/browserstorage")
    await page.click("#increaseLocalStorage", { clickCount: amountIncrease })
    expect(await page.innerText("#localStorageValue")).toBe(amountIncrease.toString())
    await page.click("#decreaseLocalStorage", { clickCount: amountDecrease })
    expect(await page.innerText("#localStorageValue")).toBe((amountIncrease - amountDecrease).toString())
})

const browserstorageTries = [
    { increase: 0, decrease: 0 },
    { increase: 0, decrease: 1 },
    { increase: 1, decrease: 0 },
    { increase: 5, decrease: 7 },
    { increase: 500, decrease: 30 },
    { increase: 123, decrease: 456 },
]
for (const { increase, decrease } of browserstorageTries) {
    test(`browserstorage with increase=${increase} and decrease=${decrease}`, async ({ page }) => {
        await page.goto("/browserstorage")

        expect(await page.innerText("#localStorageValue")).toBe("0")

        await page.click("#increaseLocalStorage", { clickCount: increase })
        await page.waitForTimeout(100)
        expect(await page.innerText("#localStorageValue")).toBe(increase.toString())

        await page.click("#decreaseLocalStorage", { clickCount: decrease })
        await page.waitForTimeout(100)
        expect(await page.innerText("#localStorageValue")).toBe((increase - decrease).toString())

        await page.click("#resetLocalStorage")
        await page.waitForTimeout(100)
        expect(await page.innerText("#localStorageValue")).toBe("0")
        expect(await page.innerText("#sessionStorageValue")).toBe("0")

        await page.click("#increaseSessionStorage", { clickCount: increase })
        await page.waitForTimeout(100)
        expect(await page.innerText("#sessionStorageValue")).toBe(increase.toString())

        await page.click("#decreaseSessionStorage", { clickCount: decrease })
        await page.waitForTimeout(100)
        expect(await page.innerText("#sessionStorageValue")).toBe((increase - decrease).toString())

        await page.click("#resetSessionStorage")
        await page.waitForTimeout(100)
        expect(await page.innerText("#sessionStorageValue")).toBe("0")
    })
}

// TODO Write benchmarks to see how long the site needs to load
