<script lang="ts">
    import { onMount } from "svelte"
    import { writable } from "svelte/store"

    import Headers from "../components/Headers.svelte"

    // Key names in local and session storage
    const localStorageKey = "localValue"
    const sessionStorageKey = "sessionValue"

    let localStorageStore
    let localStorageValue
    let sessionStorageStore
    let sessionStorageValue

    onMount(() => {
        // Get value from localStorage
        localStorageStore = writable(localStorage.getItem(localStorageKey) || "0")
        localStorageValue = parseInt(localStorage.getItem(localStorageKey)) || 0

        sessionStorageStore = writable(sessionStorage.getItem(sessionStorageKey) || "0")
        sessionStorageValue = parseInt(sessionStorage.getItem(sessionStorageKey)) || 0

        // Event based notification when a value in a store changes
        localStorageStore.subscribe((newValue) => {
            // Write to localStorage and set local value
            localStorage.setItem(localStorageKey, newValue.toString())
            localStorageValue = parseInt(newValue)
        })
        sessionStorageStore.subscribe((newValue) => {
            sessionStorage.setItem(sessionStorageKey, newValue.toString())
            sessionStorageValue = parseInt(newValue)
        })
    })
</script>

<Headers />
<div class="flex">
    <div class="m-1">Local Storage</div>
    <div class="m-1">{localStorageValue}</div>
    <button
        class="m-1"
        on:click={() => {
            localStorageStore.update((n) => (parseInt(n) + 1).toString())
        }}>Increase</button
    >
    <button
        class="m-1"
        on:click={() => {
            localStorageStore.update((n) => (parseInt(n) - 1).toString())
        }}>Decrease</button
    >
    <button
        class="m-1"
        on:click={() => {
            localStorageStore.update(() => "0")
        }}>Reset</button
    >
</div>
<div class="flex">
    <div class="m-1">Session Storage</div>
    <div class="m-1">{sessionStorageValue}</div>
    <button
        class="m-1"
        on:click={() => {
            sessionStorageStore.update((n) => (parseInt(n) + 1).toString())
        }}>Increase</button
    >
    <button
        class="m-1"
        on:click={() => {
            sessionStorageStore.update((n) => (parseInt(n) - 1).toString())
        }}>Decrease</button
    >
    <button
        class="m-1"
        on:click={() => {
            sessionStorageStore.update(() => "0")
        }}>Reset</button
    >
</div>
