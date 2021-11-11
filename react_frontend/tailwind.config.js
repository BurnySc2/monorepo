module.exports = {
    purge: {
      content: [
        "./src/**/*.{ts,tsx}",
        ],
        enabled: process.env.DEVELOPMENT !== "true" // disable purge in dev
    },
    theme: {
      extend: {},
    },
    variants: {},
    plugins: [],
  };