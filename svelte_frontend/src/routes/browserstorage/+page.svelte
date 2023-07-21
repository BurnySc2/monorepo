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

<div class="flex">
    <div class="m-1">Local Storage</div>
    <div id="localStorageValue" class="m-1">{$localStorageStore}</div>
    <button
        id="increaseLocalStorage"
        class="m-1"
        on:click={() => {
            localStorageStore.update((n) => n + 1)
        }}>Increase</button
    >
    <button
        id="decreaseLocalStorage"
        class="m-1"
        on:click={() => {
            localStorageStore.update((n) => n - 1)
        }}>Decrease</button
    >
    <button
        id="resetLocalStorage"
        class="m-1"
        on:click={() => {
            localStorageStore.update(() => 0)
        }}>Reset</button
    >
</div>
<div class="flex">
    <div class="m-1">Session Storage</div>
    <div id="sessionStorageValue" class="m-1">{$sessionStorageStore}</div>
    <button
        id="increaseSessionStorage"
        class="m-1"
        on:click={() => {
            sessionStorageStore.update((n) => n + 1)
        }}>Increase</button
    >
    <button
        id="decreaseSessionStorage"
        class="m-1"
        on:click={() => {
            sessionStorageStore.update((n) => n - 1)
        }}>Decrease</button
    >
    <button
        id="resetSessionStorage"
        class="m-1"
        on:click={() => {
            sessionStorageStore.update(() => 0)
        }}>Reset</button
    >
</div>
