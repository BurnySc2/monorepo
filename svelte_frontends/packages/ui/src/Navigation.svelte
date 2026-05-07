<script lang="ts">
import { DEV } from "esm-env"

interface App {
    name: string
    subdomain: string
    devPort: number
}

const APPS: App[] = [
    { name: "Login", subdomain: "login", devPort: 5173 },
    { name: "Audiobook", subdomain: "audiobooks", devPort: 5178 },
    { name: "TTS", subdomain: "tts", devPort: 5174 },
    { name: "Raceroom", subdomain: "raceroom", devPort: 5180 },
    { name: "Replay Pack Builder", subdomain: "replaypack", devPort: 5175 },
    { name: "Replay Comparer", subdomain: "replaycomparer", devPort: 5181 },
]

const BASE_DOMAIN = "burnysc2.xyz"

interface Props {
    currentApp?: string
}

let { currentApp = "" }: Props = $props()

function get_url(app: App): string {
    if (typeof window !== "undefined" && DEV) {
        return `http://localhost:${app.devPort}`
    }
    return `https://${app.subdomain}.${BASE_DOMAIN}`
}

function is_active(app: App): boolean {
    return currentApp === app.name
}
</script>

<nav class="nav">
    {#each APPS as app}
        {@const url = get_url(app)}
        {@const active = is_active(app)}
        <a
            href={url}
            class="nav-link {active ? 'active' : ''}"
            data-sveltekit-preload-data="hover"
        >
            {app.name}
        </a>
    {/each}
</nav>

<style>
.nav {
    display: flex;
    justify-content: center;
    padding: 0.5rem;
    background-color: #f3f4f6;
    border-bottom: 1px solid #e5e7eb;
}

.nav-link {
    margin: 0 0.125rem;
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    color: #2563eb;
    background-color: transparent;
    text-decoration: none;
    transition:
        background-color 0.15s,
        color 0.15s;
}

.nav-link:hover {
    background-color: #dbeafe;
}

.nav-link.active {
    color: white;
    background-color: #3b82f6;
    font-weight: 700;
    text-decoration: underline;
}
</style>
