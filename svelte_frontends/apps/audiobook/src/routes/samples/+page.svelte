<script lang="ts">
import type { VoiceInfo } from "@repo/api-types"
import { Spinner, toast } from "@repo/ui"
import { onMount } from "svelte"
import { generate_voice_sample, get_available_voices } from "$lib/api/audiobook"
import { matches_voice, pick_sample, SAMPLE_TEXT_VERSION } from "$lib/sample_texts"

interface CardState {
    status: "idle" | "loading" | "ready" | "error"
    audio_src: string | null
    error: string | null
}

const IDLE_CARD: CardState = { status: "idle", audio_src: null, error: null }

let voices: VoiceInfo[] = $state([])
let is_loading = $state(true)
let load_error: string | null = $state(null)
let cards = $state<Record<string, CardState>>({})
let filter_text = $state("")

let filtered = $derived(voices.filter((v) => matches_voice(v, filter_text)))
let active_count = $derived(Object.values(cards).filter((c) => c.status === "loading").length)

function list_key(voice: VoiceInfo): string {
    return `${voice.engine}|${voice.locale}|${voice.internal_name}`
}

// WHY engine+internal_name: backend resolves voices by engine_internal_name
function request_key(voice: VoiceInfo): string {
    return `${voice.engine}_${voice.internal_name}`
}

function get_card(card_key: string): CardState {
    return cards[card_key] ?? IDLE_CARD
}

function set_card(card_key: string, patch: Partial<CardState>): void {
    const current = get_card(card_key)
    cards = { ...cards, [card_key]: { ...current, ...patch } }
}

function language_name(locale: string | null | undefined): string {
    const safe_locale = String(locale ?? "")
    try {
        return new Intl.DisplayNames(["en"], { type: "language" }).of(safe_locale) ?? safe_locale
    } catch {
        return safe_locale
    }
}

function pause_others(event: Event): void {
    const current = event.currentTarget as HTMLAudioElement | null
    if (!current) {
        return
    }
    const container = current.closest("[data-samples-list]")
    container?.querySelectorAll("audio").forEach((other) => {
        const el = other as HTMLAudioElement
        if (el !== current && !el.paused) {
            el.pause()
        }
    })
}

async function load_voices(): Promise<void> {
    is_loading = true
    load_error = null
    try {
        voices = await get_available_voices()
    } catch (e) {
        console.error("Failed to load voices:", e)
        load_error = e instanceof Error ? e.message : "Failed to load voices"
    } finally {
        is_loading = false
    }
}

async function play_sample(voice: VoiceInfo): Promise<void> {
    const list_id = list_key(voice)
    const voice_id = request_key(voice)
    if (get_card(list_id).status === "loading" || active_count >= 3) {
        return
    }
    set_card(list_id, { status: "loading", error: null })
    try {
        const sample = pick_sample(voice.locale)
        const result = await generate_voice_sample(voice_id, sample.text)
        set_card(list_id, { status: "ready", audio_src: `data:audio/mpeg;base64,${result.audio_b64}` })
    } catch (e) {
        console.error("Failed to generate voice sample:", e)
        const message = e instanceof Error ? e.message : "Failed to generate sample"
        set_card(list_id, { status: "error", error: message })
        toast.error("Failed to generate voice sample")
    }
}

onMount(() => {
    void load_voices()
})
</script>

<div class="container mx-auto max-w-6xl px-4 py-8">
    <a
        href="/"
        class="btn btn-secondary mb-4"
    >
        ← Back to Books
    </a>
    <h1 class="text-3xl font-bold mb-2">Voice Samples ({filtered.length} of {voices.length} voices)</h1>
    <p class="text-sm text-gray-600 mb-4">
        Tap Play to hear a sample of each voice. Sample text v{SAMPLE_TEXT_VERSION}.
        {#if active_count > 0}
            ({active_count}
            loading…)
        {/if}
    </p>
    <input
        type="search"
        bind:value={filter_text}
        placeholder="Filter by language... e.g. german, deutsch, de"
        aria-label="Filter voices by language"
        class="input input-bordered w-full max-w-md mb-6"
    >
    {#if is_loading}
        <div class="flex justify-center py-12"><Spinner /></div>
    {:else if load_error}
        <div class="text-center py-12">
            <p class="text-red-600 mb-4">{load_error}</p>
            <button
                type="button"
                class="btn btn-primary"
                onclick={() => void load_voices()}
            >
                Retry
            </button>
        </div>
    {:else}
        <div
            class="grid grid-cols-1 gap-4"
            data-samples-list
        >
            {#each filtered as voice (list_key(voice))}
                <div class="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                    <h3 class="text-lg font-semibold text-gray-900">{voice.label}</h3>
                    <div class="flex flex-wrap gap-2 mt-2">
                        <span class="text-xs bg-gray-100 text-gray-700 rounded px-2 py-1">{voice.locale}</span>
                        <span class="text-xs bg-gray-100 text-gray-700 rounded px-2 py-1">{voice.engine}</span>
                        <span class="text-xs bg-gray-100 text-gray-700 rounded px-2 py-1">{voice.gender}</span>
                        <span class="text-xs bg-blue-50 text-blue-700 rounded px-2 py-1">
                            {language_name(voice.locale)}
                        </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-3">
                        {pick_sample(voice.locale).text}
                    </p>
                    <div class="mt-4 flex items-center gap-2">
                        <button
                            type="button"
                            class="btn btn-primary"
                            disabled={get_card(list_key(voice)).status === "loading" || active_count >= 3}
                            aria-busy={get_card(list_key(voice)).status === "loading"}
                            onclick={() => void play_sample(voice)}
                            aria-label={get_card(list_key(voice)).audio_src
                                ? `Replay sample for ${voice.label}`
                                : `Play sample for ${voice.label}`}
                        >
                            {#if get_card(list_key(voice)).status === "loading"}
                                <Spinner />
                                Loading…
                            {:else if get_card(list_key(voice)).audio_src}
                                Replay
                            {:else}
                                Play
                            {/if}
                        </button>
                    </div>
                    {#if get_card(list_key(voice)).audio_src}
                        <!-- biome-ignore lint/a11y/useMediaCaption: generated TTS preview has no captions file; full sample text shown as transcript in card -->
                        <audio
                            class="mt-3 w-full"
                            controls
                            src={get_card(list_key(voice)).audio_src}
                            onplay={pause_others}
                        ></audio>
                    {/if}
                    {#if get_card(list_key(voice)).error}
                        <p class="text-sm text-red-600 mt-2">{get_card(list_key(voice)).error}</p>
                    {/if}
                    {#if get_card(list_key(voice)).status === "error"}
                        <button
                            type="button"
                            class="btn btn-secondary mt-2"
                            disabled={active_count >= 3}
                            onclick={() => void play_sample(voice)}
                        >
                            Retry
                        </button>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
