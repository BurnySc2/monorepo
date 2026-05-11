<script lang="ts">
import { onDestroy } from "svelte"

// State initialized from URL params
let stream_name = $state("")
let read_name_lang = $state("")
let volume = $state(1.0) // 0 to 1
let is_loaded = $state(false)

const api_target = import.meta.env?.VITE_API_TARGET || "localhost:8000"
const ws_backend_server_url = import.meta.env?.VITE_API_TARGET ? `wss://${api_target}` : `ws://${api_target}`
let ws: WebSocket | null = null
let data: string | null = $state(null)

// WebSocket reconnection with exponential backoff
function connect_ws(ws_url: string) {
    ws = new WebSocket(ws_url)

    ws.addEventListener("open", () => {
        is_loaded = true
    })

    ws.addEventListener("message", (event) => {
        const message = JSON.parse(event.data)
        data = `data:audio/mpeg;base64,${message.data}`
    })

    ws.addEventListener("close", () => {
        // Reconnect with exponential backoff
        const max_delay = 30_000 // 30 seconds
        const stored_attempts = Number(sessionStorage.getItem("ws_reconnect_attempts") || "0")
        const delay = Math.min(1000 * 2 ** stored_attempts, max_delay)
        sessionStorage.setItem("ws_reconnect_attempts", String(stored_attempts + 1))
        setTimeout(() => connect_ws(ws_url), delay)
    })
}

function on_play_end() {
    data = null
}

// Initialize from URL params and connect WebSocket
$effect(() => {
    const params = new URLSearchParams(window.location.search)
    stream_name = params.get("stream_name") ?? ""
    read_name_lang = params.get("read_name_lang") ?? "none"
    const vol_param = params.get("volume")
    if (vol_param) {
        volume = Number(vol_param) / 100
    }

    if (stream_name) {
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
            id="audio"
            controls
            autoplay
            onended={on_play_end}
            src={data}
            {volume}
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
    transition: opacity 5s ease-out 5s;
}

.fade-out-element.loaded {
    opacity: 0;
}
</style>
