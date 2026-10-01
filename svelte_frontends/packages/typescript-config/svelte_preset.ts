import adapter from "@sveltejs/adapter-static"
import type { Config } from "@sveltejs/kit"
import { vitePreprocess } from "@sveltejs/vite-plugin-svelte"

type SveltePresetOptions = {
    with_base?: boolean
}

export function create_svelte_config(options: SveltePresetOptions = {}): Config {
    const { with_base = true } = options
    const config: Config = {
        preprocess: vitePreprocess(),
        kit: {
            adapter: adapter({
                fallback: "404.html",
                precompress: false,
                strict: true,
            }),
            ...(with_base
                ? {
                      paths: {
                          base: (process.argv.includes("dev") ? "" : process.env.BASE_PATH) as "" | undefined,
                      },
                  }
                : {}),
        },
    }
    return config
}
