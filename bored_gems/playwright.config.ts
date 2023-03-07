import type { PlaywrightTestConfig } from "@playwright/test"

const config: PlaywrightTestConfig = {
    webServer: {
        command: "npm run build && vite preview --port 2987",
        port: 2987,
    },
    repeatEach: 1,
    timeout: 5000,
}

export default config
