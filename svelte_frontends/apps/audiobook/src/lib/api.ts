const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export const fetch_login_status = async () => {
    const resp = await fetch(`${get_api_base()}/login`)
    return resp.json()
}
