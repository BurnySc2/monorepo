export function get_api_base(): string {
    const raw_target =
        typeof import.meta.env === "undefined" ? undefined : (import.meta.env.VITE_API_TARGET as string | undefined)
    if (!raw_target) {
        return "http://localhost:8000"
    }
    const without_scheme = raw_target.replace(/^https?:\/\//i, "").replace(/\/+$/, "")
    if (!without_scheme) {
        return "http://localhost:8000"
    }
    const host_port = without_scheme.split("/")[0] ?? ""
    const lower_host_port = host_port.toLowerCase()
    let hostname: string
    if (lower_host_port.startsWith("[")) {
        const end = lower_host_port.indexOf("]")
        hostname = end === -1 ? lower_host_port : lower_host_port.slice(1, end)
    } else if (lower_host_port === "::1" || lower_host_port.startsWith("::1:")) {
        hostname = "::1"
    } else {
        hostname = lower_host_port.split(":")[0] ?? ""
    }
    const is_local =
        hostname === "localhost" || hostname.endsWith(".localhost") || hostname === "127.0.0.1" || hostname === "::1"
    const protocol = is_local ? "http" : "https"
    return `${protocol}://${without_scheme}`
}
