<script lang="ts">
interface Props {
    url: string
    mime_type: string
    onclose: () => void
}

let { url, mime_type, onclose }: Props = $props()

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
        class="flex h-full w-full flex-col items-center justify-center p-1"
        onclick={(e) => e.stopPropagation()}
    >
        {#if mime_type.startsWith("video/")}
            <video
                class="grow object-contain"
                controls
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
            <audio
                class="w-full"
                controls
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
