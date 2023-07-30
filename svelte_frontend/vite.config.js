import { sveltekit } from "@sveltejs/kit/vite"
import { defineConfig } from "vitest/config"

/** @type {import('vite').UserConfig} */
export default defineConfig({
    plugins: [sveltekit()],
    define: {
        "process.env": process.env,
    },
    optimizeDeps: {
        exclude: ["@ffmpeg/ffmpeg", "@ffmpeg/util"],
    },
})
