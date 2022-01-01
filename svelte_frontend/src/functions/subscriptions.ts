import { GRAPHQL_WS_ENDPOINT } from "./constants"
import { createClient } from "graphql-ws"

export const subscribe = (
    query: string,
    // Define what happens when data was received
    onNext: (data: any) => void
): (() => void) => {
    {
        // https://github.com/enisdenjo/graphql-ws#use-the-client
        const client = createClient({
            url: GRAPHQL_WS_ENDPOINT,
        })
        // Declare a unsubscribe function
        let unsubscribe: () => void

        // Define subscription
        const subscribe = async () => {
            unsubscribe = client.subscribe(
                {
                    query: query,
                },
                {
                    next: onNext,
                    error: (_error) => {
                        console.log("Error")
                    },
                    complete: () => {
                        console.log("Subscription ended?")
                    },
                }
            )
        }
        // Start subscription
        subscribe()
        return unsubscribe
    }
}
