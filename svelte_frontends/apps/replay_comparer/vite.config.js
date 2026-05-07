import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

const api_target = process.env.VITE_API_TARGET ? `https://${process.env.VITE_API_TARGET}` : "http://localhost:8000"

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        port: 5181,
        strictPort: true,
        proxy: {
            "/parse_replay": {
                target: api_target,
                changeOrigin: true,
            },
            "/get_replay_events": {
                target: api_target,
                changeOrigin: true,
            },
        },
    },
})
