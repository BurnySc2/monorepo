import adapter from "@sveltejs/adapter-static"
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

/** @typedef {{ with_base?: boolean }} SveltePresetOptions */
/** @typedef {import("@sveltejs/kit").Config} Config */
/**
 * @param {SveltePresetOptions} [options]
 * @returns {Config}
 */
export function create_svelte_config(options = {}) {
    const { with_base = true } = options
    const config = {
        preprocess: vitePreprocess(),
        kit: {
            adapter: adapter({ fallback: "404.html", precompress: false, strict: true }),
            ...(with_base
                ? {
                      paths: {
                          base: process.argv.includes("dev") ? "" : process.env.BASE_PATH,
                      },
                  }
                : {}),
        },
    }
    return config
}
