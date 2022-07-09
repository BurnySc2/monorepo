import type { PlaywrightTestConfig } from "@playwright/test"

const config: PlaywrightTestConfig = {
    webServer: {
        command: "npm run build && vite preview --port 2987",
        port: 2987,
    },
}

export default config
