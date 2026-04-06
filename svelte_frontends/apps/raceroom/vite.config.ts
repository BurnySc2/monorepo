import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

export default defineConfig({
    server: {
        port: 5180,
        strictPort: true,
        proxy: {
            "/api": {
                target: "http://0.0.0.0:8000",
                changeOrigin: true,
            },
        },
    },
    plugins: [tailwindcss(), sveltekit()],
})
