<script lang="ts">
    import { onMount } from "svelte"
    import type { VoiceInfo } from "@repo/api-types"
    import { Spinner, toast } from "@repo/ui"
    import { generate_voice_sample, get_available_voices } from "$lib/api/audiobook"
    import { SAMPLE_TEXT_VERSION, pickSample } from "$lib/sample_texts"

    const MAX_CACHED_SAMPLES = 30

    let voices: VoiceInfo[] = $state([])
    let is_loading = $state(true)
    let load_error: string | null = $state(null)
    let audio_map = $state(new Map<string, string>())
    let statuses = $state(new Map<string, string>())
    let voice_errors = $state(new Map<string, string>())

    let active_count = $derived([...statuses.values()].filter((s) => s === "loading").length)
    let generate_disabled = $derived(active_count >= 3)

    function list_key(voice: VoiceInfo): string {
        return `${voice.engine}|${voice.locale}|${voice.internal_name}`
    }

    function request_key(voice: VoiceInfo): string {
        return `${voice.engine}_${voice.label.replace(/ /g, "_")}`
    }

    function language_name(locale: string): string {
        try {
            return new Intl.DisplayNames(["en"], { type: "language" }).of(locale) ?? locale
        } catch {
            return locale
        }
    }

    function pause_others(event: Event): void {
        const current = event.currentTarget as HTMLAudioElement | null
        if (!current) {
            return
        }
        document.querySelectorAll("audio").forEach((other) => {
            const el = other as HTMLAudioElement
            if (el !== current && !el.paused) {
                el.pause()
            }
        })
    }

    function store_audio(voice_key: string, data_url: string): void {
        if (!audio_map.has(voice_key) && audio_map.size >= MAX_CACHED_SAMPLES) {
            const oldest = audio_map.keys().next().value
            if (oldest !== undefined) {
                audio_map.delete(oldest)
            }
        }
        audio_map.set(voice_key, data_url)
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
        if (statuses.get(list_id) === "loading" || generate_disabled) {
            return
        }
        statuses.set(list_id, "loading")
        voice_errors.delete(list_id)
        try {
            const sample = pickSample(voice.locale)
            const result = await generate_voice_sample(voice_id, sample.text)
            store_audio(list_id, `data:audio/mpeg;base64,${result.audio_b64}`)
            statuses.set(list_id, "idle")
        } catch (e) {
            console.error("Failed to generate voice sample:", e)
            const message = e instanceof Error ? e.message : "Failed to generate sample"
            statuses.set(list_id, "error")
            voice_errors.set(list_id, message)
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
    <h1 class="text-3xl font-bold mb-2">Voice Samples ({voices.length} voices)</h1>
    <p class="text-sm text-gray-600 mb-6">
        Tap Play to hear a sample of each voice. Sample text v{SAMPLE_TEXT_VERSION}.
        {#if active_count > 0}
            ({active_count} loading…)
        {/if}
    </p>

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
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            {#each voices as voice (list_key(voice))}
                {@const list_id = list_key(voice)}
                {@const status = statuses.get(list_id) ?? "idle"}
                {@const audio_src = audio_map.get(list_id)}
                {@const voice_error = voice_errors.get(list_id)}
                {@const sample = pickSample(voice.locale)}
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
                    <p class="text-sm text-gray-600 mt-3">{sample.text}</p>
                    <div class="mt-4">
                        <button
                            type="button"
                            class="btn btn-primary"
                            disabled={status === "loading" || generate_disabled}
                            onclick={() => void play_sample(voice)}
                            aria-label={audio_src
                                ? `Replay sample for ${voice.label}`
                                : `Play sample for ${voice.label}`}
                        >
                            {#if status === "loading"}
                                <Spinner /> Loading…
                            {:else if audio_src}
                                Replay
                            {:else}
                                Play
                            {/if}
                        </button>
                    </div>
                    {#if audio_src}
                        <audio
                            class="mt-3 w-full"
                            controls
                            src={audio_src}
                            onplay={pause_others}
                        ></audio>
                    {/if}
                    {#if voice_error}
                        <p class="text-sm text-red-600 mt-2">{voice_error}</p>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
