import { defineConfig } from "vitest/config"

export default defineConfig({
    test: {
        include: ["src/**/*.test.ts"],
        exclude: ["dist/**", ".svelte-kit/**", "**/*.test.tsx"],
        coverage: {
            provider: "v8",
            include: ["src/**/*.ts"],
            exclude: ["**/*.test.ts", "dist/**", ".svelte-kit/**"],
        },
    },
})
