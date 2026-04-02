import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

export default defineConfig({
    plugins: [tailwindcss(), sveltekit()],
    server: {
        // Fix the port for login page for redirect
        port: 5173,
        // Optional: fail if the port is already in use (helps catch stray processes)
        strictPort: true,
    },
})
