import { GraphQLClient } from "graphql-request"

export const ip = process.env.BACKEND_SERVER || "localhost:8000"
const https: boolean = ip.indexOf("localhost") === -1
const HTTP_OR_HTTPS = https ? "https" : "http"

// Graphql
export const GRAPHQL_ENDPOINT = `${HTTP_OR_HTTPS}://${ip}/graphql`
export const GRAPHQL_WS_ENDPOINT = `ws://${ip}/graphql`
export const GRAPHQL_CLIENT = new GraphQLClient(GRAPHQL_ENDPOINT, { credentials: "include" })

// Rest
export const LOGIN_ENDPOINT = `${HTTP_OR_HTTPS}://${ip}/login`
