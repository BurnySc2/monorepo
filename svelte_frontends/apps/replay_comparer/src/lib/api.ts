const get_api_base = () => {
    const target = import.meta.env.VITE_API_TARGET
    const protocol = target?.includes("localhost") ? "http" : "https"
    return target ? `${protocol}://${target}` : "http://localhost:8000"
}

export const fetch_parse_replay = async (replay_file: File, replay_tick: string) => {
    const formData = new FormData()
    formData.append("replay_tick", replay_tick)
    formData.append("replay_file", replay_file)

    const resp = await fetch(`${get_api_base()}/api/replay_comparer/parse_replay`, {
        method: "POST",
        body: formData,
    })
    return resp.json()
}

export const fetch_replay_events = async (replay_file: File) => {
    const formData = new FormData()
    formData.append("replay_file", replay_file)

    const resp = await fetch(`${get_api_base()}/api/replay_comparer/get_replay_events`, {
        method: "POST",
        body: formData,
    })
    return resp.json()
}
