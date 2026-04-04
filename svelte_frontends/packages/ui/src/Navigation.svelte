<script lang="ts">
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
        { name: "Telegram", subdomain: "tbrowser", devPort: 5179 },
        { name: "Replay Pack Builder", subdomain: "replaypack", devPort: 5175 },
    ]

    const BASE_DOMAIN = "burnysc2.xyz"

    interface Props {
        currentApp?: string
    }

    let { currentApp = "" }: Props = $props()

    function getUrl(app: App): string {
        if (typeof window !== "undefined" && import.meta.env.DEV) {
            return `http://localhost:${app.devPort}`
        }
        return `https://${app.subdomain}.${BASE_DOMAIN}`
    }

    function isActive(app: App): boolean {
        return currentApp === app.name
    }
</script>

<nav class="flex justify-center space-x-1 p-2 bg-gray-100 border-b border-gray-200">
    {#each APPS as app}
        {@const url = getUrl(app)}
        {@const active = isActive(app)}
        <a
            href={url}
            class="px-3 py-1 rounded text-sm transition-colors {active
                ? 'bg-blue-500 text-white font-bold underline'
                : 'text-blue-600 hover:bg-blue-100'}"
        >
            {app.name}
        </a>
    {/each}
</nav>
