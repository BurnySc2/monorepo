import adapter from "@sveltejs/adapter-static"
import preprocess from "svelte-preprocess"

const baseUrl = process.env.BASE_URL || ""

/** @type {import('@sveltejs/kit').Config} */
const config = {
    // Consult https://github.com/sveltejs/svelte-preprocess
    // for more information about preprocessors
    preprocess: preprocess(),

    kit: {
        // hydrate the <div id="svelte"> element in src/app.html
        adapter: adapter({
            // default options are shown
            pages: "build",
            assets: "build",
            fallback: null,
        }),
        prerender: {
            // This can be false if you're using a fallback (i.e. SPA mode)
            default: true,
        },
        paths: {
            base: baseUrl,
        },
        appDir: "internal",
        // Make env variables available and accessable in frontend
        vite: {
            define: {
                "process.env": process.env,
            },
        },
    },
}

export default config
