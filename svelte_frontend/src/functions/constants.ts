export const ip = process.env.BACKEND_SERVER || "localhost:8000"
const https: boolean = ip.indexOf("localhost") === -1
const HTTP_OR_HTTPS = https ? "https" : "http"

// Rest
export const LOGIN_ENDPOINT = `${HTTP_OR_HTTPS}://${ip}/login`
