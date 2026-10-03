<script lang="ts">
import { is_local_host } from "@repo/api-client"
import { calculate_reconnect_delay, clamp_volume_ratio } from "$lib/utils"

// State initialized from URL params
// Volume convention: ratio 0-1 for HTMLAudioElement; default 1.0 (full volume).
let stream_name = $state("")
let read_name_lang = $state("")
let volume = $state(1.0) // 0 to 1
let is_loaded = $state(false)

const raw_api_target = (import.meta.env?.VITE_API_TARGET as string | undefined) || "localhost:8000"
const cleaned_api_target = raw_api_target.replace(/^https?:\/\//i, "").replace(/\/+$/, "")
function is_local_ws_target(target: string): boolean {
    return is_local_host(target)
}
const ws_protocol = is_local_ws_target(cleaned_api_target) ? "ws" : "wss"
const ws_backend_server_url = `${ws_protocol}://${cleaned_api_target}`
let ws: WebSocket | null = null
let data: string | null = $state(null)
let reconnect_timer: ReturnType<typeof setTimeout> | null = null

// WebSocket reconnection with exponential backoff
function connect_ws(ws_url: string) {
    ws = new WebSocket(ws_url)

    ws.addEventListener("open", () => {
        is_loaded = true
        sessionStorage.setItem("ws_reconnect_attempts", "0")
    })

    ws.addEventListener("message", (event) => {
        try {
            const message: unknown = JSON.parse(event.data)
            if (typeof message !== "object" || message === null || !("data" in message)) {
                return
            }
            const audio_data = (message as { data: unknown }).data
            if (typeof audio_data !== "string" || audio_data.length === 0) {
                return
            }
            data = `data:audio/mpeg;base64,${audio_data}`
        } catch {
            return
        }
    })

    ws.addEventListener("close", () => {
        // Reconnect with exponential backoff
        const raw_attempts = Number(sessionStorage.getItem("ws_reconnect_attempts") || "0")
        const stored_attempts = Number.isFinite(raw_attempts) && raw_attempts >= 0 ? Math.floor(raw_attempts) : 0
        const delay = calculate_reconnect_delay(stored_attempts)
        sessionStorage.setItem("ws_reconnect_attempts", String(Math.min(stored_attempts + 1, 10)))
        if (reconnect_timer) {
            clearTimeout(reconnect_timer)
        }
        reconnect_timer = setTimeout(() => connect_ws(ws_url), delay)
    })

    ws.addEventListener("error", () => {
        ws?.close()
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
    if (vol_param !== null) {
        const parsed = Number(vol_param)
        volume = clamp_volume_ratio(Number.isFinite(parsed) ? parsed / 100 : 1.0)
    }

    if (stream_name) {
        const ws_url = `${ws_backend_server_url}/tts-api/ws/${encodeURIComponent(stream_name)}/${encodeURIComponent(read_name_lang)}`
        connect_ws(ws_url)
    }

    return () => {
        if (reconnect_timer) {
            clearTimeout(reconnect_timer)
            reconnect_timer = null
        }
        ws?.close()
    }
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
