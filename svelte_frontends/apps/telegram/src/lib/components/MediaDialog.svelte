<script lang="ts">
import {
    initial_media_viewer_state,
    media_load_failed,
    media_load_started,
    media_loaded,
} from "$lib/media_viewer_state"

interface Props {
    url: string
    mime_type: string
    onclose: () => void
}

let { url, mime_type, onclose }: Props = $props()

let media_state = $state(initial_media_viewer_state())

let previous_media_key = ""

$effect(() => {
    // Reset loading/error state whenever the dialog content (URL or type) changes.
    const next_media_key = `${url}|${mime_type}`
    if (next_media_key !== previous_media_key) {
        previous_media_key = next_media_key
        media_state = media_load_started()
    }
})

function handle_media_error() {
    media_state = media_load_failed()
}

function handle_media_loaded() {
    media_state = media_loaded()
}

function handle_close() {
    onclose()
}

function handle_keydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
        handle_close()
    }
}
</script>

<svelte:window onkeydown={handle_keydown} />

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<dialog
    open
    class="fixed inset-0 z-50 flex h-full w-full items-center justify-center bg-black/50 backdrop-blur-sm"
    onclick={handle_close}
    onkeydown={handle_keydown}
    aria-modal="true"
>
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="relative flex h-full w-full flex-col items-center justify-center p-1"
        onclick={(e) => e.stopPropagation()}
    >
        {#if media_state.error_message}
            <div
                role="alert"
                class="m-4 flex max-w-lg flex-col items-center justify-center gap-2 rounded-xl bg-gray-800/90 p-6 text-center ring-1 ring-white"
            >
                <div class="text-white">{media_state.error_message}</div>
                <div class="text-sm text-gray-400">Check the file or try downloading it instead.</div>
            </div>
        {:else if mime_type.startsWith("video/")}
            {#if media_state.is_loading}
                <div
                    role="status"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 p-8 text-white"
                >
                    <div class="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
                    <span>Loading media...</span>
                </div>
            {/if}
            <video
                class="grow object-contain"
                class:hidden={media_state.is_loading}
                controls
                onerror={handle_media_error}
                onloadeddata={handle_media_loaded}
            >
                <source
                    src={url}
                    type={mime_type}
                >
                <track
                    kind="captions"
                    srclang="en"
                    label="English"
                    src=""
                >
                Your browser does not support the video tag.
            </video>
        {:else if mime_type.startsWith("audio/")}
            {#if media_state.is_loading}
                <div
                    role="status"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 p-8 text-white"
                >
                    <div class="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
                    <span>Loading media...</span>
                </div>
            {/if}
            <audio
                class="w-full"
                class:hidden={media_state.is_loading}
                controls
                onerror={handle_media_error}
                onloadeddata={handle_media_loaded}
            >
                <source
                    src={url}
                    type={mime_type}
                >
                <track
                    kind="captions"
                    srclang="en"
                    label="English"
                    src=""
                >
                Your browser does not support the audio element.
            </audio>
        {:else if mime_type.startsWith("image/")}
            <img
                class="max-h-full object-scale-down"
                src={url}
                alt="Media"
            >
        {:else}
            <div class="text-white">Unsupported media type: {mime_type}</div>
        {/if}

        <button
            class="mt-4 rounded-xl bg-gray-700 p-2 text-white ring-1 ring-white hover:bg-green-700"
            type="button"
            onclick={handle_close}
        >
            Close
        </button>
    </div>
</dialog>
