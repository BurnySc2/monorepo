import { createClient } from "graphql-ws"

export const subscribe = (
    endpoint_url: string | (() => string | Promise<string>),
    query: string,
    // Define what happens when data was received
    onNext: (data: any) => void
): (() => void) => {
    // https://github.com/enisdenjo/graphql-ws#use-the-client
    // Create client
    const client = createClient({
        url: endpoint_url,
    })
    {
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
