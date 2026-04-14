<script lang="ts">
import type { VoiceOption } from "@repo/api-types"
import { onMount } from "svelte"

let voices = $state<VoiceOption[]>([])
let selected_voice = $state("")
let user_text = $state("")
let audio_b64 = $state("")
let is_generating = $state(false)

let twitch_channel = $state("burnysc2")
let twitch_volume = $state(15)

async function load_voices() {
    try {
        const resp = await fetch("/tts-generate/voices")
        if (resp.ok) {
            voices = await resp.json()
            if (voices.length > 0) {
                selected_voice = voices[0].value
            }
        }
    } catch (e) {
        console.error("Failed to load voices", e)
    }
}

onMount(() => {
    load_voices()
})

async function generate_audio() {
    is_generating = true
    const voice = selected_voice
    const text = user_text
    try {
        const resp = await fetch("/tts-generate/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ voice, text }),
        })
        if (resp.ok) {
            const data = await resp.json()
            audio_b64 = data.audio_b64
        } else {
            console.error("TTS request failed", resp.status)
        }
    } catch (e) {
        console.error("Error generating TTS", e)
    } finally {
        is_generating = false
    }
}

async function copy_to_clipboard(text: string) {
    await navigator.clipboard.writeText(text)
}

const preview_text = $derived(`${selected_voice.toLowerCase()}: ${user_text}`)
const overlay_url = $derived(`https://burnysc2.xyz/tts-api/twitch/${twitch_channel}?volume=${twitch_volume}`)
</script>

<main class="p-4 max-w-xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">Text‑to‑Speech Generator</h1>
    <label class="block mb-2"
        >Voice:
        <select
            bind:value={selected_voice}
            class="border rounded w-full p-1"
        >
            {#each voices as voice}
                <option value={voice.value}>{voice.label}</option>
            {/each}
        </select>
    </label>
    <label class="block mb-2"
        >Text to convert:
        <textarea
            bind:value={user_text}
            rows="3"
            class="border rounded w-full p-1"
        ></textarea>
    </label>
    <button
        onclick={generate_audio}
        disabled={user_text.trim() === '' || is_generating}
        class="bg-blue-600 text-white py-1 px-3 rounded disabled:opacity-50 mb-4"
    >
        {is_generating ? 'Generating...' : 'Generate audio'}
    </button>
    {#if audio_b64}
        <audio
            controls
            class="w-full mb-4"
        >
            <track
                kind="captions"
                src=""
                srclang="en"
                label="English"
            >
            <source
                src="data:audio/mpeg;base64,{audio_b64}"
                type="audio/mpeg"
            >
            Your browser does not support the audio element.
        </audio>
    {/if}
    <div class="flex items-center mb-2">
        <input
            type="text"
            readonly
            value={preview_text}
            class="flex-1 border rounded p-1"
        >
        <button
            onclick={() => copy_to_clipboard(preview_text)}
            class="ml-2 bg-gray-200 p-1 rounded"
        >
            Copy
        </button>
    </div>
    <h2 class="text-xl font-semibold mt-6 mb-2">OBS Overlay Setup</h2>
    <p class="mb-2">Add the following URL as a browser source in OBS (replace the channel name if needed):</p>
    <div class="flex items-center mb-2">
        <input
            type="text"
            readonly
            value={overlay_url}
            class="flex-1 border rounded p-1"
        >
        <button
            onclick={() => copy_to_clipboard(overlay_url)}
            class="ml-2 bg-gray-200 p-1 rounded"
        >
            Copy
        </button>
    </div>
    <label class="block mb-2"
        >Twitch channel name:
        <input
            type="text"
            bind:value={twitch_channel}
            class="border rounded w-full p-1"
        >
    </label>
    <label class="block mb-4"
        >Volume (0‑100):
        <input
            type="number"
            min="0"
            max="100"
            bind:value={twitch_volume}
            class="border rounded w-full p-1"
        >
    </label>
</main>

<style>
main {
    font-family: system-ui, sans-serif;
}
</style>
