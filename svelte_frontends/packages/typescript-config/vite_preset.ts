import { sveltekit } from "@sveltejs/kit/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"

export function create_vite_config(port: number) {
    return defineConfig({
        plugins: [tailwindcss(), sveltekit()],
        server: { port, strictPort: true },
        preview: { port, strictPort: true },
    })
}
