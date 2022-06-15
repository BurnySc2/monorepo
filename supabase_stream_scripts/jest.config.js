export default {
    testEnvironment: "jsdom",
    transform: {
        "\\.js$": "babel-jest",
        "^.+\\.ts$": "ts-jest",
        "^.+\\.svelte$": ["svelte-jester", { preprocess: true }],
    },
    moduleFileExtensions: ["js", "ts", "svelte"],
}
