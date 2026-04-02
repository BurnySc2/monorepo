<script lang="ts">
import { onDestroy, onMount } from "svelte"
// Simple reconnection logic for WebSocket (no external package)
export let stream_name: string = ""
export let read_name_lang: string = ""
export let volume: number = 1.0
const ws_backend_server_url = import.meta.env.VITE_WS_BACKEND_URL || ""
let ws: WebSocket | null = null

// Initialise parameters and WebSocket on mount
onMount(() => {
    const params = new URLSearchParams(window.location.search)
    if (!stream_name) {
        stream_name = params.get("stream_name") ?? ""
    }
    if (!read_name_lang) {
        read_name_lang = params.get("read_name_lang") ?? ""
    }
    if (volume === 1.0) {
        const vol = params.get("volume")
        if (vol) {
            volume = Number(vol)
        }
    }

    const ws_url = `${ws_backend_server_url}/tts-api/ws/${stream_name}/${read_name_lang}`
    // Simple reconnection logic: attempt to reconnect with exponential backoff
    const maxDelay = 30000 // 30 seconds max
    let reconnectAttempts = 0
    function connect() {
        ws = new WebSocket(ws_url)
        ws.addEventListener("open", () => {
            reconnectAttempts = 0 // reset on successful connection
        })
        ws.addEventListener("close", () => {
            const delay = Math.min(1000 * 2 ** reconnectAttempts, maxDelay)
            reconnectAttempts++
            setTimeout(connect, delay)
        })
    }
    connect()

    if (ws) {
        ws.addEventListener("message", (event) => {
            const audio_el = document.getElementById("audio") as HTMLAudioElement | null
            if (audio_el) {
                // Assume server sends base64 audio data
                audio_el.src = `data:audio/mpeg;base64,${event.data}`
                audio_el.volume = volume
                audio_el.play().catch(() => {})
            }
        })
    }
})

// Clean up WebSocket when component is destroyed
onDestroy(() => {
    ws?.close()
})
</script>

<div class="flex h-screen flex-col items-center justify-center">
    <div
        id="content"
        class="fade-out-element"
    >
        <audio
            controls
            id="audio"
        >
            <track
                kind="captions"
                src=""
                srclang="en"
                label="English"
            >
            Your browser does not support the audio element.
        </audio>
    </div>
</div>

<style>
.fade-out-element {
    opacity: 1;
    transition: opacity 10s ease-out;
    transition-delay: 5s;
}
</style>
