import adapter from "@sveltejs/adapter-static"
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

// See https://svelte.dev/docs/kit/adapter-static#GitHub-Pages
const config = {
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter({
            fallback: "404.html",
            precompress: false,
            strict: true,
        }),
        paths: {
            base: process.argv.includes("dev") ? "" : process.env.BASE_PATH,
        },
    },
}

export default config
