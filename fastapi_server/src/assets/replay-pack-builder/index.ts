const drop_zone = document.getElementById('drop-zone') as HTMLDivElement | null
const file_input = document.getElementById('replays') as HTMLInputElement | null


type Status = "uploaded" | "processing" | "processed" | "error"

type FileData = {
    file: File
    md5: string
    status: Status
}

type ReplayPlayer = {
    clan_tag: string
    name: string
    pick_race: "Random" | "Protoss" | "Terran" | "Zerg"
    play_race: "Protoss" | "Terran" | "Zerg"
    is_human: boolean
    mmr: number | null
}

type ReplayTeam = {
    result: "Win" | "Loss"
    players: ReplayPlayer[]
}

type ReplayData = FileData & {
    // Per player data
    teams: ReplayTeam[]

    played_timestamp: number
    game_length_seconds: number
    map_name: string
    region_short: "us" | "eu" | "kr"
    expansion: "WoL" | "HotS" | "LotV"
    game_base_build: number
    game_version: string
    game_type: string
    is_ladder: boolean
    is_private: boolean
    resume_from_replay: boolean
}

type ReplayFilter = {
    filter_enabled: boolean
    game_matchmaking: boolean
    game_custom: boolean
    game_coop: boolean
    game_arcade: boolean
    game_include_games_with_ai: boolean
    game_include_games_resumed_from_replay: boolean
    expansion_wol: boolean
    expansion_hots: boolean
    expansion_lotv: boolean
    server_americas: boolean
    server_europe: boolean
    server_asia: boolean
    player_name_must_include: string
    player_name_must_exclude: string
    date_played_min: string
    date_played_max: string
    game_duration_min: string
    game_duration_max: string
    player_count_min: number
    player_count_max: number
    average_mmr_min: number
    average_mmr_max: number
    matchup_pvp: boolean
    matchup_pvt: boolean
    matchup_pvz: boolean
    matchup_tvt: boolean
    matchup_tvz: boolean
    matchup_zvz: boolean
    map_name_must_include: string
    map_name_must_exclude: string
}

let FILES: FileData[] = []
let PARSED: ReplayData[] = []
let FILTERED: ReplayData[] = []

const calculate_md5 = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        const spark = new (window as any).SparkMD5.ArrayBuffer()

        reader.onload = (e: ProgressEvent<FileReader>) => {
            if (e.target === null) {
                reject(new Error('FileReader event target is null'))
                return
            }
            spark.append(e.target.result as ArrayBuffer)
            const hash = spark.end()
            resolve(hash)
        }

        reader.onerror = (e) => reject(e)
        reader.readAsArrayBuffer(file)
    })
}

async function download_files_as_zip() {
    // Check if there are files to zip
    if (FILTERED.length === 0) {
        alert("No files to download!")
        return
    }

    // Create a new JSZip instance
    const zip = new (window as any).JSZip()

    // Add each file to the ZIP
    const rename_pattern = (document.querySelector("#name_template") as HTMLInputElement).value
    for (const file_data of FILTERED) {
        // Use the file name from the File object and its content
        const new_file_name = get_replay_name_from_template(rename_pattern, file_data)
        zip.file(`${new_file_name}.SC2Replay`, file_data.file)
    }

    try {
        // Generate the ZIP file as a blob
        const zip_blob = await zip.generateAsync({ type: "blob" })

        // Create a temporary URL for the blob
        const url = window.URL.createObjectURL(zip_blob)

        // Create a temporary link element to trigger the download
        const link = document.createElement("a")
        link.href = url
        link.download = "downloaded_files.zip" // Name of the downloaded ZIP file
        document.body.appendChild(link)
        link.click()

        // Clean up
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
    } catch (error) {
        console.error("Error creating ZIP file:", error)
        alert("Failed to create ZIP file. Please try again.")
    }
}

const replay_passes_filter = (filter_settings: ReplayFilter, replay: ReplayData): boolean => {
    // Filter is disabled, allow all replays to pass
    if (!filter_settings.filter_enabled) {
        return true
    }

    // Filter does not allow matchmaking games but replay is a matchmaking game
    if (!filter_settings.game_matchmaking && replay.is_ladder) {
        console.log("Replay does not pass 'game_matchmaking' filter")
        return false
    }
    if (!filter_settings.game_custom && replay.is_private) {
        console.log("Replay does not pass 'game_custom' filter")
        return false
    }
    // TODO coop replays
    // if (filter_settings.game_coop){
    //     return false
    // }
    // TODO arcade replays
    // if (filter_settings.game_arcade){
    //     return false
    // }

    // Remove replays with computer / AI
    const replay_has_computers = replay.teams.reduce((bool: boolean, team: ReplayTeam): boolean => {
        if (bool) {
            return bool
        }
        for (const player of team.players) {
            if (!player.is_human) {
                return true
            }
        }
        return false
    }, false)
    if (!filter_settings.game_include_games_with_ai && replay_has_computers) {
        console.log("Replay does not pass 'game_include_games_with_ai' filter")
        return false
    }

    // Remove replays that were resumed from replay
    if (!filter_settings.game_include_games_resumed_from_replay && replay.resume_from_replay) {
        console.log("Replay does not pass 'game_include_games_resumed_from_replay' filter")
        return false
    }

    // Expansion filter
    if (!filter_settings.expansion_wol && replay.expansion === "WoL") {
        console.log("Replay does not pass 'expansion_wol' filter")
        return false
    }
    if (!filter_settings.expansion_hots && replay.expansion === "HotS") {
        console.log("Replay does not pass 'expansion_hots' filter")
        return false
    }
    if (!filter_settings.expansion_lotv && replay.expansion === "LotV") {
        console.log("Replay does not pass 'expansion_lotv' filter")
        return false
    }

    // Server filter
    if (!filter_settings.server_americas && replay.region_short === "us") {
        console.log("Replay does not pass 'server_americas' filter")
        return false
    }
    if (!filter_settings.server_europe && replay.region_short === "eu") {
        console.log("Replay does not pass 'server_europe' filter")
        return false
    }
    if (!filter_settings.server_asia && replay.region_short === "kr") {
        console.log("Replay does not pass 'server_asia' filter")
        return false
    }

    // Date played filter
    const timestamp_parse = (date_string: string): number => {
        return Date.parse(date_string)
    }
    if (filter_settings.date_played_min !== "" && replay.played_timestamp < timestamp_parse(filter_settings.date_played_min)) {
        console.log("Replay does not pass 'date_played_min' filter")
        return false
    }
    if (filter_settings.date_played_max !== "" && timestamp_parse(filter_settings.date_played_max) < replay.played_timestamp) {
        console.log("Replay does not pass 'date_played_max' filter")
        return false
    }

    // Game duration filter
    const game_duration_parse = (game_duration: string): number => {
        const [minutes_str, seconds_str] = game_duration.split(":")
        const total_seconds = Number(minutes_str) * 60 + Number(seconds_str)
        return total_seconds
    }
    // Empty string if not set, otherwise format "mm:ss"
    if (filter_settings.game_duration_min !== "" && replay.game_length_seconds < game_duration_parse(filter_settings.game_duration_min)) {
        console.log("Replay does not pass 'game_duration_min' filter")
        return false
    }
    if (filter_settings.game_duration_max !== "" && game_duration_parse(filter_settings.game_duration_max) < replay.game_length_seconds) {
        console.log("Replay does not pass 'game_duration_max' filter")
        return false
    }

    // Calculate average mmr of players
    const average_mmr = replay.teams.reduce((average: number[], team: ReplayTeam) => {
        let current_average = [...average]
        for (const player of team.players) {
            if (player.mmr !== null) {
                current_average.push(player.mmr)
            }
        }
        return current_average
    }, []).reduce((my_sum: number, current: number, index: number, array: number[]) => {
        let current_sum = my_sum
        if (current_sum < 0) {
            current_sum = 0
        }
        if (index + 1 === array.length) {
            return my_sum / array.length
        }
        return my_sum + current
    }, -1)
    // Min mmr filter, inactive if filter value === 0
    if (filter_settings.average_mmr_min !== 0 && average_mmr !== -1 && average_mmr < filter_settings.average_mmr_min) {
        console.log("Replay does not pass 'average_mmr_min' filter")
        return false
    }
    if (filter_settings.average_mmr_max !== 0 && average_mmr !== -1 && filter_settings.average_mmr_max < average_mmr) {
        console.log("Replay does not pass 'average_mmr_max' filter")
        return false
    }

    // Conditions: Needs to be a 1v1 (2 teams, 2 players)
    const teams_count = replay.teams.length
    const players_count = replay.teams.reduce((count: number, team: ReplayTeam) => {
        let current_count = count
        for (const player of team.players) {
            current_count += 1
        }
        return current_count
    }, 0)

    // Player count filter
    if (filter_settings.player_count_min !== 0 && players_count < filter_settings.player_count_min) {
        console.log("Replay does not pass 'player_count_min' filter")
        return false
    }
    if (filter_settings.player_count_max !== 0 && filter_settings.player_count_max < players_count) {
        console.log("Replay does not pass 'player_count_max' filter")
        return false
    }

    // Matchup filter
    if (teams_count === 2 && players_count === 2) {
        const player1_race = replay.teams[0].players[0].play_race[0] as "P" | "T" | "Z"
        const player2_race = replay.teams[1].players[0].play_race[0] as "P" | "T" | "Z"
        const player_races = [player1_race, player2_race]
        player_races.sort()
        const matchup = player_races.join("v")
        if (!filter_settings.matchup_pvp && matchup === "PvP") {
            console.log("Replay does not pass 'matchup_pvp' filter")
            return false
        }
        if (!filter_settings.matchup_pvt && matchup === "PvT") {
            console.log("Replay does not pass 'matchup_pvt' filter")
            return false
        }
        if (!filter_settings.matchup_pvz && matchup === "PvZ") {
            console.log("Replay does not pass 'matchup_pvz' filter")
            return false
        }
        if (!filter_settings.matchup_tvt && matchup === "TvT") {
            console.log("Replay does not pass 'matchup_tvt' filter")
            return false
        }
        if (!filter_settings.matchup_tvz && matchup === "TvZ") {
            console.log("Replay does not pass 'matchup_tvz' filter")
            return false
        }
        if (!filter_settings.matchup_zvz && matchup === "ZvZ") {
            console.log("Replay does not pass 'matchup_zvz' filter")
            return false
        }
    }

    // Player name include / exclude filter
    const all_player_names = replay.teams.reduce((player_names: string[], team: ReplayTeam) => {
        let current_player_names = [...player_names]
        for (const player of team.players) {
            if (!player.is_human) { continue }
            current_player_names.push(player.name.toLowerCase())
        }
        return current_player_names
    }, [])
    // Player name must-include filter
    if (filter_settings.player_name_must_include.trim() !== "") {
        const player_names_must_include = filter_settings.player_name_must_include.split(",").map((value: string) => {
            return value.trim().toLowerCase()
        })
        let player_found = false
        for (const player of all_player_names) {
            for (const search_string of player_names_must_include) {
                if (player.indexOf(search_string) !== -1) {
                    player_found = true
                    break
                }
            }
        }
        if (!player_found) {
            console.log("Replay does not pass 'player_name_must_include' filter")
            return false
        }
    }
    // Player name must-exclude filter
    if (filter_settings.player_name_must_exclude.trim() !== "") {
        const player_names_must_exclude = filter_settings.player_name_must_exclude.split(",").map((value: string) => {
            return value.trim().toLowerCase()
        })
        for (const player of all_player_names) {
            for (const search_string of player_names_must_exclude) {
                if (player.indexOf(search_string) !== -1) {
                    console.log("Replay does not pass 'player_name_must_exclude' filter")
                    return false
                }
            }
        }
    }

    // Map name include / exclude filter
    // Map name must-include filter
    if (filter_settings.map_name_must_include.trim() !== "") {
        const map_names_must_include = filter_settings.map_name_must_include.split(",").map((value: string) => {
            return value.trim().toLowerCase()
        })
        let map_found = false
        for (const search_string of map_names_must_include) {
            if (replay.map_name.indexOf(search_string) !== -1) {
                map_found = true
                break
            }
        }
        if (!map_found) {
            console.log("Replay does not pass 'map_name_must_include' filter")
            return false
        }
    }
    // Map name must-exclude filter
    if (filter_settings.map_name_must_exclude.trim() !== "") {
        const map_names_must_exclude = filter_settings.map_name_must_exclude.split(",").map((value: string) => {
            return value.trim().toLowerCase()
        })
        for (const search_string of map_names_must_exclude) {
            if (replay.map_name.indexOf(search_string) !== -1) {
                console.log("Replay does not pass 'map_name_must_exclude' filter")
                return false
            }
        }
    }

    // Default: pass the filter
    return true
}

const filter_replays = (): void => {
    let filter_settings: ReplayFilter = {
        filter_enabled: (document.querySelector("#filter_enabled") as HTMLInputElement).checked,
        game_matchmaking: (document.querySelector("#matchmaking") as HTMLInputElement).checked,
        game_custom: (document.querySelector("#custom") as HTMLInputElement).checked,
        game_coop: (document.querySelector("#coop") as HTMLInputElement).checked,
        game_arcade: (document.querySelector("#arcade") as HTMLInputElement).checked,
        game_include_games_with_ai: (document.querySelector("#games_with_ai") as HTMLInputElement).checked,
        game_include_games_resumed_from_replay: (document.querySelector("#resume_from_replay") as HTMLInputElement).checked,
        expansion_wol: (document.querySelector("#expansion_wol") as HTMLInputElement).checked,
        expansion_hots: (document.querySelector("#expansion_hots") as HTMLInputElement).checked,
        expansion_lotv: (document.querySelector("#expansion_lotv") as HTMLInputElement).checked,
        server_americas: (document.querySelector("#server_americas") as HTMLInputElement).checked,
        server_europe: (document.querySelector("#server_europe") as HTMLInputElement).checked,
        server_asia: (document.querySelector("#server_asia") as HTMLInputElement).checked,
        player_name_must_include: (document.querySelector("#player_names_include") as HTMLInputElement).value,
        player_name_must_exclude: (document.querySelector("#player_names_exclude") as HTMLInputElement).value,
        date_played_min: (document.querySelector("#date_min") as HTMLInputElement).value,
        date_played_max: (document.querySelector("#date_max") as HTMLInputElement).value,
        game_duration_min: (document.querySelector("#duration_min") as HTMLInputElement).value,
        game_duration_max: (document.querySelector("#duration_max") as HTMLInputElement).value,
        player_count_min: Number((document.querySelector("#player_count_min") as HTMLInputElement).value),
        player_count_max: Number((document.querySelector("#player_count_max") as HTMLInputElement).value),
        average_mmr_min: Number((document.querySelector("#mmr_min") as HTMLInputElement).value),
        average_mmr_max: Number((document.querySelector("#mmr_max") as HTMLInputElement).value),
        matchup_pvp: (document.querySelector("#matchup_pvp") as HTMLInputElement).checked,
        matchup_pvt: (document.querySelector("#matchup_pvt") as HTMLInputElement).checked,
        matchup_pvz: (document.querySelector("#matchup_pvz") as HTMLInputElement).checked,
        matchup_tvt: (document.querySelector("#matchup_tvt") as HTMLInputElement).checked,
        matchup_tvz: (document.querySelector("#matchup_tvz") as HTMLInputElement).checked,
        matchup_zvz: (document.querySelector("#matchup_zvz") as HTMLInputElement).checked,
        map_name_must_include: (document.querySelector("#map_names_include") as HTMLInputElement).value,
        map_name_must_exclude: (document.querySelector("#map_names_exclude") as HTMLInputElement).value,
    }

    console.log(filter_settings)

    const filtered: ReplayData[] = []
    for (const replay of PARSED) {
        if (replay.status !== "processed") {
            continue
        }
        if (replay_passes_filter(filter_settings, replay)) {
            filtered.push(replay)
        }
    }
    FILTERED = filtered

    document.querySelector("#download_button")!.textContent = `Zip and download ${FILTERED.length} Replays`
}


const get_replay_name_from_template = (template: string, replay: ReplayData): string => {
    type TempPlayer = {
        name: string
        race: "Protoss" | "Terran" | "Zerg"
        mmr: number
    }
    let player1: TempPlayer = {
        name: "",
        race: "Protoss",
        mmr: 0,
    }
    let player2: TempPlayer = {
        name: "",
        race: "Protoss",
        mmr: 0,
    }
    if (0 < replay.teams.length) {
        player1 = {
            name: replay.teams[0].players[0].name,
            race: replay.teams[0].players[0].play_race,
            mmr: replay.teams[0].players[0].mmr ?? 0,
        }
        if (1 < replay.teams.length) {
            player2 = {
                name: replay.teams[1].players[0].name,
                race: replay.teams[1].players[0].play_race,
                mmr: replay.teams[1].players[0].mmr ?? 0,
            }
        }
    }

    const replay_date = new Date(replay.played_timestamp).toISOString().split("T")[0].replace(/-/g, "_")
    const replay_time = new Date(replay.played_timestamp).toISOString().split("T")[1].split(".")[0].replace(/:/g, "_")
    const [minutes, seconds] = [replay.game_length_seconds / 60, replay.game_length_seconds % 60]
    const placeholders = {
        date: replay_date,
        time: replay_time,
        duration: `${Math.round(minutes)}m` + `${seconds}`.padStart(2, "0") + "s",
        map: replay.map_name.replace(/ /g, "_"),
        region: replay.region_short,
        REGION: replay.region_short.toUpperCase(),
        version: replay.game_version,
        p1name: player1.name,
        p1race: player1.race,
        p1r: player1.race[0],
        p1mmr: player1.mmr,
        p2name: player2.name,
        p2race: player2.race,
        p2r: player2.race[0],
        p2mmr: player2.mmr,
    }

    let replaced_string = template
    for (const key of Object.keys(placeholders)) {
        replaced_string = replaced_string.replace(`\{${key}\}`, placeholders[key])
    }
    return replaced_string
}

const prevent_defaults = (e: Event) => {
    e.preventDefault()
    e.stopPropagation()
}

const init_drop_zone = () => {
    if (!drop_zone || !file_input) {
        console.error('Required elements not found')
        return
    }
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event_name => {
        document.body.addEventListener(event_name, prevent_defaults, false)
    });

    // Highlight drop zone when dragging files over
    ['dragenter', 'dragover'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault()
            drop_zone.classList.add('border-blue-500', 'bg-blue-100')
        }, false)
    });

    ['dragleave', 'drop'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault()
            drop_zone.classList.remove('border-blue-500', 'bg-blue-100')
        }, false)
    })

    // Handle dropped files
    drop_zone.addEventListener('drop', async (e: DragEvent) => {
        e.preventDefault()

        if (!e.dataTransfer) {
            return
        }

        // Parse file in frontend, calculate md5
        const md5s = [...FILES, ...PARSED].map(file => file.md5)
        for (let file of e.dataTransfer.files) {
            let md5 = await calculate_md5(file)
            // Don't add duplicates
            if (md5s.includes(md5)) { continue }
            FILES.push({
                file,
                md5,
                status: "uploaded",
            })
            md5s.push(md5)
            // console.log('File:', file.name, 'MD5:', md5)
        }

        // Add files to input element
        const data_transfer = new DataTransfer()
        for (const file of FILES) {
            data_transfer.items.add(file.file)
        }
        file_input.files = data_transfer.files
    })
}

const init_filter_event_listeners = () => {
    // Whenever a filter changes, parse all files and check if they pass the filter
    let timer
    function debounce(func, timeout = 500) {
        clearTimeout(timer)
        timer = setTimeout(() => {
            func()
        }, timeout)
    }

    const element_ids_instant_filter = ["filter_enabled", "matchmaking", "custom", "coop", "arcade", "games_with_ai", "resume_from_replay", "expansion_wol", "expansion_hots", "expansion_lotv", "server_americas", "server_europe", "server_asia", "matchup_pvp", "matchup_pvt", "matchup_pvz", "matchup_tvt", "matchup_tvz", "matchup_zvz"]
    for (const element_id of element_ids_instant_filter) {
        document.querySelector(`#${element_id}`)!.addEventListener("change", () => {
            filter_replays()
        })
    }

    const element_ids_debounce_filter = ["player_names_include", "player_names_exclude", "date_min", "date_max", "duration_min", "duration_max", "player_count_min", "player_count_max", "mmr_min", "mmr_max", "map_names_include", "map_names_exclude"]
    for (const element_id of element_ids_debounce_filter) {
        document.querySelector(`#${element_id}`)!.addEventListener("input", () => {
            debounce(() => {
                filter_replays()
            })
        })
    }
}

const init_template_listener = () => {
    const update_example_name_template = () => {
        const rename_pattern = (document.querySelector("#name_template") as HTMLInputElement).value;
        (document.querySelector("#name_example") as HTMLInputElement).value = get_replay_name_from_template(rename_pattern,
            // Example replay data
            {
                file: new File([], "test"),
                md5: "12345",
                status: "processed",
                teams: [
                    {
                        result: "Win",
                        players: [{
                            clan_tag: "Heroes",
                            name: "BuRny",
                            pick_race: "Terran",
                            play_race: "Terran",
                            is_human: true,
                            mmr: 420,
                        }]
                    },
                    {
                        result: "Loss",
                        players: [{
                            clan_tag: "",
                            name: "Computer (Easy)",
                            pick_race: "Random",
                            play_race: "Zerg",
                            is_human: false,
                            mmr: 42,
                        }]
                    },
                ],
                played_timestamp: Date.now(),
                game_length_seconds: 1337,
                map_name: "Alcyone LE",
                region_short: "eu",
                expansion: "LotV",
                game_base_build: 1234,
                game_version: "5.0.14",
                game_type: "idk",
                is_ladder: false,
                is_private: false,
                resume_from_replay: false,
            })
    }

    update_example_name_template()
    document.querySelector("#name_template")!.addEventListener("input", () => {
        update_example_name_template()
    })
}

const parse_replay = async (file_data: FileData): Promise<ReplayData> => {
    const form_data = new FormData()
    form_data.append('file', file_data.file)

    const response = await fetch('/sc2-replay-pack-builder/parse-replay', {
        method: 'POST',
        body: form_data,
    })

    if (!response.ok) {
        throw new Error(`Failed to parse replay: ${response.statusText}`)
    }

    return await response.json()
}

const process_files = async () => {
    let new_files_processed = false
    for (const file_data of [...FILES]) {
        if (file_data.status !== 'uploaded') continue
        new_files_processed = true

        try {
            file_data.status = 'processing'
            const replay_data = await parse_replay(file_data)
            PARSED.push({
                ...file_data,
                ...replay_data,
                status: 'processed'
            })
            FILES = FILES.filter(f => f.md5 !== file_data.md5)
        } catch (error) {
            console.error('Error parsing replay:', error)
            file_data.status = 'error'
        }
    }

    // Trigger filter replays
    if (new_files_processed) {
        filter_replays()
    }
}

const main = (): void => {
    init_drop_zone()
    init_filter_event_listeners()
    init_template_listener()
    console.log("Replay pack builder initialized")
    setInterval(process_files, 1000)
}

main()