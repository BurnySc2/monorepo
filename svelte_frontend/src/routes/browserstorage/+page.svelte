<script lang="ts">
    import { onMount } from "svelte"
    import { writable, type Writable } from "svelte/store"

    // Key names in local and session storage
    const localStorageKey = "localValue"
    const sessionStorageKey = "sessionValue"

    // Store values
    let localStorageStore: Writable<number>
    let sessionStorageStore: Writable<number>

    onMount(() => {
        // Get value from localStorage
        localStorageStore = writable(Number(localStorage.getItem(localStorageKey)) ?? 0)

        sessionStorageStore = writable(Number(sessionStorage.getItem(sessionStorageKey)) ?? 0)

        // Event based notification when a value in a store changes
        localStorageStore.subscribe((newValue) => {
            // Write to localStorage and set local value
            localStorage.setItem(localStorageKey, String(newValue))
        })
        sessionStorageStore.subscribe((newValue) => {
            sessionStorage.setItem(sessionStorageKey, String(newValue))
        })
    })
</script>

<body>
    <div>
        <div>Local Storage</div>
        <div id="localStorageValue">{$localStorageStore}</div>
        <button
            id="increaseLocalStorage"
            on:click={() => {
                localStorageStore.update((n) => n + 1)
            }}>Increase</button
        >
        <button
            id="decreaseLocalStorage"
            on:click={() => {
                localStorageStore.update((n) => n - 1)
            }}>Decrease</button
        >
        <button
            id="resetLocalStorage"
            on:click={() => {
                localStorageStore.update(() => 0)
            }}>Reset</button
        >
    </div>
    <div>
        <div>Session Storage</div>
        <div id="sessionStorageValue">{$sessionStorageStore}</div>
        <button
            id="increaseSessionStorage"
            on:click={() => {
                sessionStorageStore.update((n) => n + 1)
            }}>Increase</button
        >
        <button
            id="decreaseSessionStorage"
            on:click={() => {
                sessionStorageStore.update((n) => n - 1)
            }}>Decrease</button
        >
        <button
            id="resetSessionStorage"
            on:click={() => {
                sessionStorageStore.update(() => 0)
            }}>Reset</button
        >
    </div>
</body>

<style>
    body > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
    }
    body > div > * {
        margin: 0.5rem;
    }
</style>
