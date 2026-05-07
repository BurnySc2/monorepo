import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

const api_target = process.env.VITE_API_TARGET ? `https://${process.env.VITE_API_TARGET}` : "http://localhost:8000"

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        port: 5178,
        strictPort: true,
        proxy: {
            "/api": {
                target: api_target,
                changeOrigin: true,
            },
            "/tts-generate": {
                target: api_target,
                changeOrigin: true,
            },
        },
    },
})
