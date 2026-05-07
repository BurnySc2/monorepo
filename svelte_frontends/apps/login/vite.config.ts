import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

const api_target = process.env.VITE_API_TARGET ? `https://${process.env.VITE_API_TARGET}` : "http://localhost:8000"

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        // Fix the port for login page for redirect
        port: 5173,
        // Optional: fail if the port is already in use (helps catch stray processes)
        strictPort: true,
        proxy: {
            "/login": {
                target: api_target,
                changeOrigin: true,
            },
            "/logout": {
                target: api_target,
                changeOrigin: true,
            },
        },
    },
})
