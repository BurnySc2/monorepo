<script lang="ts">
import type { VoiceInfo } from "@repo/api-types"
import { Spinner } from "@repo/ui"
import { onMount } from "svelte"
import { tts_settings } from "$lib/tts_settings.svelte"

let voices = $state<VoiceInfo[]>([])
let user_text = $state("")
let audio_b64 = $state("")
let is_generating = $state(false)
let is_loading_voices = $state(true)
let copied_preview = $state(false)
let copied_overlay = $state(false)

let twitch_channel = $state("burnysc2")
let twitch_volume = $state(15)

async function load_voices() {
    try {
        const resp = await fetch("/tts-generate/voices")
        if (resp.ok) {
            voices = await resp.json()
        }
    } catch (e) {
        console.error("Failed to load voices", e)
    } finally {
        is_loading_voices = false
    }
}

onMount(() => {
    load_voices()
})

async function generate_audio() {
    is_generating = true
    audio_b64 = ""
    const voice = voices[tts_settings.selected_voice_index]
    const text = user_text
    try {
        const resp = await fetch("/tts-generate/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ voice: `${voice.engine}_${voice.label.replace(/ /g, "_")}`, text }),
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

async function handle_copy_preview() {
    await navigator.clipboard.writeText(preview_text)
    copied_preview = true
    setTimeout(() => {
        copied_preview = false
    }, 2500)
}

async function handle_copy_overlay() {
    await navigator.clipboard.writeText(overlay_url)
    copied_overlay = true
    setTimeout(() => {
        copied_overlay = false
    }, 2500)
}

const preview_text = $derived.by(() => {
    if (voices.length === 0) {
        return ""
    }

    return `${voices[tts_settings.selected_voice_index].engine}_${voices[tts_settings.selected_voice_index].label.toLowerCase().replaceAll(" ", "_")}: ${user_text}`
})
const api_target = import.meta.env?.VITE_API_TARGET || "localhost:5174"
const overlay_url = $derived(
    import.meta.env?.VITE_API_TARGET
        ? `https://${api_target}/overlay?stream_name=${twitch_channel}&volume=${twitch_volume}`
        : `http://${api_target}/overlay?stream_name=${twitch_channel}&volume=${twitch_volume}`,
)
</script>

<main class="flex flex-col p-4 max-w-xl mx-auto gap-4">
    <h1 class="text-2xl font-bold">Text-to-Speech Generator</h1>
    {#if is_loading_voices}
        <div class="flex justify-center p-8"><Spinner /></div>
    {:else}
        <div class="card">
            <label class="block mb-2"
                >Voice:
                <select
                    bind:value={tts_settings.selected_voice_index}
                    class="input w-full"
                >
                    {#each voices as voice, index}
                        <option value={index}>{voice.locale} {voice.engine} {voice.label} ({voice.gender})</option>
                    {/each}
                </select>
            </label>
            <label class="block mb-2"
                >Text to convert:
                <textarea
                    bind:value={user_text}
                    rows="3"
                    class="input w-full"
                ></textarea>
            </label>
            <button
                onclick={generate_audio}
                disabled={user_text.trim() === '' || is_generating}
                class="btn-primary w-full"
            >
                {is_generating ? 'Generating...' : 'Generate audio'}
            </button>
        </div>

        {#if is_generating}
            <div class="self-center"><Spinner /></div>
        {:else if audio_b64}
            <div class="card">
                <audio
                    controls
                    class="w-full"
                    volume={tts_settings.audio_volume / 100}
                    onvolumechange={(e) => {
                        const target = e.currentTarget as HTMLAudioElement;
                        const volume = Math.round(target.volume * 100);
                        tts_settings.audio_volume = Math.min(100, Math.max(0, volume));
                    }}
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
            </div>
        {/if}

        <div class="card">
            <div>Text copyable to twitch chat:</div>
            <div class="flex items-center mb-2">
                <input
                    type="text"
                    readonly
                    value={preview_text}
                    class="input flex-1"
                >
                <button
                    onclick={handle_copy_preview}
                    class="btn-secondary ml-2"
                >
                    {copied_preview ? 'Copied!' : 'Copy'}
                </button>
            </div>
        </div>

        <div class="card">
            <h2 class="text-xl font-semibold mb-2">OBS Overlay Setup</h2>
            <p class="text-sm text-gray-600 mb-2">
                Add the following URL as a browser source in OBS (replace the channel name if needed):
            </p>
            <div class="flex items-center mb-2">
                <input
                    type="text"
                    readonly
                    value={overlay_url}
                    class="input flex-1"
                >
                <button
                    onclick={handle_copy_overlay}
                    class="btn-secondary ml-2"
                >
                    {copied_overlay ? 'Copied!' : 'Copy'}
                </button>
            </div>
            <label class="block mb-2"
                >Twitch channel name:
                <input
                    type="text"
                    bind:value={twitch_channel}
                    class="input w-full"
                >
            </label>
            <label class="block"
                >Volume (0-100):
                <input
                    type="number"
                    min="0"
                    max="100"
                    bind:value={twitch_volume}
                    class="input w-full"
                >
            </label>
        </div>
    {/if}
</main>
