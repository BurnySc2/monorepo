import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

/**
 * @param {number} port
 * @returns {import("vite").UserConfig}
 */
export function create_vite_config(port) {
    return defineConfig({
        plugins: [tailwindcss(), sveltekit()],
        server: { port, strictPort: true },
        preview: { port, strictPort: true },
    })
}
