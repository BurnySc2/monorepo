export const ip = process.env.BACKEND_SERVER || "localhost:8000"
const https: boolean = ip.indexOf("localhost") === -1
const HTTP_OR_HTTPS = https ? "https" : "http"

// Rest
export const API_SERVER_ADDRESS = `${HTTP_OR_HTTPS}://${ip}`
export const API_ENDPOINT = `${API_SERVER_ADDRESS}/api`
export const API_BODY_ENDPOINT = `${API_SERVER_ADDRESS}/api_body`
export const API_MODEL_ENDPOINT = `${API_SERVER_ADDRESS}/api_model`
