import preprocess from "svelte-preprocess"
import adapter from "@sveltejs/adapter-static"
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
