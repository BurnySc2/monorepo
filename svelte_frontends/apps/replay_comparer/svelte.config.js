import adapter from "@sveltejs/adapter-static"
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

const config = {
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter({
            fallback: "404.html",
            precompress: false,
            strict: true,
        }),
    },
}

export default config
