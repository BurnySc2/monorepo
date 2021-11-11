const fetch2 = async (url: string, requestOptions: RequestInit = {}): Promise<Response> => {
    // Make use of env variable "REACT_APP_PROXY" because react doesnt let you override the package.json "proxy" setting with an env variable
    // If env variable is not set, use empty string and use default from package.json "proxy"
    const address = process.env.REACT_APP_PROXY
    if (!address) {
        console.error("process.env.REACT_APP_PROXY is not set! Check your Env variables")
    }
    return await fetch(`${address}${url}`, requestOptions)
}

export const get = async (url: string): Promise<Response> => {
    return await fetch2(url)
}

export const post = async (url: string, body: Record<string, unknown> = {}): Promise<Response> => {
    const requestOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    }
    return await fetch2(url, requestOptions)
}

export const delete_ = async (url: string): Promise<Response> => {
    const requestOptions = {
        method: "DELETE",
    }
    return await fetch2(url, requestOptions)
}
