<script lang="ts">
    import { onMount } from 'svelte';
    import { writable } from 'svelte/store';

    // State variables (snake_case as requested)
    const voices_list: string[] = [];
    const selected_voice = writable('');
    const user_text = writable('');
    const audio_b64 = writable('');
    const is_generating = writable(false);
    const twitch_channel = writable('burnysc2');
    const twitch_volume = writable(15);

    // Load voices on mount (you could fetch from an endpoint if available)
    onMount(() => {
        // Static list – replace with fetch if needed
        const available = [
            'alice',
            'bob',
            'charlie'
        ];
        voices_list.push(...available.sort());
        if (voices_list.length > 0) {
            selected_voice.set(voices_list[0]);
        }
    });

    // Generate audio by calling the FastAPI TTS endpoint
    async function generate_audio() {
        is_generating.set(true);
        const voice = get(selected_voice);
        const text = get(user_text);
        try {
            const resp = await fetch('/tts-api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ voice, text })
            });
            if (resp.ok) {
                const data = await resp.json();
                // Expect { audio_b64: string }
                audio_b64.set(data.audio_b64);
            } else {
                console.error('TTS request failed', resp.status);
            }
        } catch (e) {
            console.error('Error generating TTS', e);
        } finally {
            is_generating.set(false);
        }
    }

    // Helper to copy text to clipboard
    async function copy_to_clipboard(text: string) {
        await navigator.clipboard.writeText(text);
    }

    // Derived values
    $: preview_text = `${$selected_voice.toLowerCase()}: ${$user_text}`;
    $: overlay_url = `https://burnysc2.xyz/tts-api/twitch/${$twitch_channel}?volume=${$twitch_volume}`;
</script>

<main class="p-4 max-w-xl mx-auto">
    <h1 class="text-2xl font-bold mb-4">Text‑to‑Speech Generator</h1>

    <!-- Voice selector -->
    <label class="block mb-2">
        Voice:
        <select bind:value={$selected_voice} class="border rounded w-full p-1">
            {#each voices_list as voice}
                <option value={voice}>{voice}</option>
            {/each}
        </select>
    </label>

    <!-- Text input -->
    <label class="block mb-2">
        Text to convert:
        <textarea bind:value={$user_text} rows="3" class="border rounded w-full p-1"></textarea>
    </label>

    <!-- Generate button -->
    <button on:click={generate_audio}
            disabled={$user_text.trim() === '' || $is_generating}
            class="bg-blue-600 text-white py-1 px-3 rounded disabled:opacity-50 mb-4">
        {$is_generating ? 'Generating...' : 'Generate audio'}
    </button>

    <!-- Audio preview -->
    {#if $audio_b64}
        <audio controls class="w-full mb-4">
            <track kind="captions" src="" srclang="en" label="English" />
            <source src="data:audio/mpeg;base64,{$audio_b64}" type="audio/mpeg" />
            Your browser does not support the audio element.
        </audio>
    {/if}

    <!-- Copy preview text -->
    <div class="flex items-center mb-2">
        <input type="text" readonly value={preview_text} class="flex-1 border rounded p-1" />
        <button on:click={() => copy_to_clipboard(preview_text)} class="ml-2 bg-gray-200 p-1 rounded">Copy</button>
    </div>

    <h2 class="text-xl font-semibold mt-6 mb-2">OBS Overlay Setup</h2>
    <p class="mb-2">Add the following URL as a browser source in OBS (replace the channel name if needed):</p>

    <div class="flex items-center mb-2">
        <input type="text" readonly value={overlay_url} class="flex-1 border rounded p-1" />
        <button on:click={() => copy_to_clipboard(overlay_url)} class="ml-2 bg-gray-200 p-1 rounded">Copy</button>
    </div>

    <label class="block mb-2">
        Twitch channel name:
        <input type="text" bind:value={$twitch_channel} class="border rounded w-full p-1" />
    </label>
    <label class="block mb-4">
        Volume (0‑100):
        <input type="number" min="0" max="100" bind:value={$twitch_volume} class="border rounded w-full p-1" />
    </label>
</main>

<style>
    main { font-family: system-ui, sans-serif; }
</style>
