import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

const api_target = process.env.VITE_API_TARGET || "http://0.0.0.0:8000"

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        port: 5174,
        proxy: {
            "/tts-generate": {
                target: api_target,
                changeOrigin: true,
            },
        },
    },
})
