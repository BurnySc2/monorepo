<script lang="ts">
import { onDestroy } from "svelte"

// State initialized from URL params
let stream_name = $state("")
let read_name_lang = $state("")
let volume = $state(1.0)
let is_loaded = $state(false)

const ws_backend_server_url = import.meta.env.VITE_WS_BACKEND_URL || ""
let ws: WebSocket | null = null

// WebSocket reconnection with exponential backoff
function connect_ws(ws_url: string) {
    ws = new WebSocket(ws_url)

    ws.addEventListener("open", () => {
        is_loaded = true
    })

    ws.addEventListener("message", (event) => {
        const audio_el = document.getElementById("audio") as HTMLAudioElement | null
        if (audio_el) {
            // Server sends base64 audio data
            audio_el.src = `data:audio/mpeg;base64,${event.data}`
            audio_el.volume = volume
            audio_el.play().catch(() => {
                // Ignore autoplay errors
            })
        }
    })

    ws.addEventListener("close", () => {
        // Reconnect with exponential backoff
        const max_delay = 30000 // 30 seconds
        const stored_attempts = Number(sessionStorage.getItem("ws_reconnect_attempts") || "0")
        const delay = Math.min(1000 * 2 ** stored_attempts, max_delay)
        sessionStorage.setItem("ws_reconnect_attempts", String(stored_attempts + 1))
        setTimeout(() => connect_ws(ws_url), delay)
    })
}

// Initialize from URL params and connect WebSocket
$effect(() => {
    const params = new URLSearchParams(window.location.search)
    stream_name = params.get("stream_name") ?? ""
    read_name_lang = params.get("read_name_lang") ?? ""
    const vol_param = params.get("volume")
    if (vol_param) {
        volume = Number(vol_param)
    }

    if (stream_name && read_name_lang) {
        const ws_url = `${ws_backend_server_url}/tts-api/ws/${stream_name}/${read_name_lang}`
        connect_ws(ws_url)
    }

    return () => {
        ws?.close()
    }
})

onDestroy(() => {
    ws?.close()
})
</script>

<div class="flex h-screen flex-col items-center justify-center">
    <div
        id="content"
        class="fade-out-element"
        class:loaded={is_loaded}
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
    transition: opacity 10s ease-out 5s;
}

.fade-out-element.loaded {
    opacity: 0;
}
</style>
