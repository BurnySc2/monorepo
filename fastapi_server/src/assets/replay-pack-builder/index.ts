const drop_zone = document.getElementById('drop-zone') as HTMLDivElement | null
const file_input = document.getElementById('replays') as HTMLInputElement | null


type Status = "uploaded" | "processing" | "processed" | "error"

type FileData = {
    file: File
    md5: string
    status: Status
}

type ReplayData = FileData & {
    // Per player data
    // TODO player names? clan names? player races? player mmr? player spawn location?
    teams: string[][]

    // Global data
    game_type: "custom" | "ladder" | "resume_from_replay"
    // 0, 1, 2, 3 whichever team won
    // -1 for draw
    map_name: string
    date_time_played: number
    game_length_seconds: number
    region_short: "na" | "eu" | "kr"
    expansion: "WoL" | "HotS" | "LotV"
}

type ReplayFilter = {
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
    date_played_min: number
    date_played_max: number
    game_duration_min: number
    game_duration_max: number
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
        const reader = new FileReader();
        const spark = new (window as any).SparkMD5.ArrayBuffer();

        reader.onload = (e: ProgressEvent<FileReader>) => {
            if (e.target === null) {
                reject(new Error('FileReader event target is null'));
                return;
            }
            spark.append(e.target.result as ArrayBuffer);
            const hash = spark.end();
            resolve(hash);
        };

        reader.onerror = (e) => reject(e);
        reader.readAsArrayBuffer(file);
    });
};

async function download_files_as_zip() {
    // Check if there are files to zip
    if (FILES.length === 0) {
        alert("No files to download!");
        return;
    }

    // Create a new JSZip instance
    const zip = new (window as any).JSZip();

    // Add each file to the ZIP
    for (const fileData of FILES) {
        // Use the file name from the File object and its content
        zip.file(fileData.file.name, fileData.file);
    }

    try {
        // Generate the ZIP file as a blob
        const zipBlob = await zip.generateAsync({ type: "blob" });

        // Create a temporary URL for the blob
        const url = window.URL.createObjectURL(zipBlob);

        // Create a temporary link element to trigger the download
        const link = document.createElement("a");
        link.href = url;
        link.download = "downloaded_files.zip"; // Name of the downloaded ZIP file
        document.body.appendChild(link);
        link.click();

        // Clean up
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error creating ZIP file:", error);
        alert("Failed to create ZIP file. Please try again.");
    }
}

const replay_passes_filter = (filter_settings: ReplayFilter, replay: ReplayData): boolean => {
    // TODO implement
    return true
}

const filter_replays = (): void => {
    let filter_settings: ReplayFilter = {
        game_matchmaking: (document.querySelector("#matchmaking") as HTMLInputElement).checked,
        game_custom: (document.querySelector("#custom") as HTMLInputElement).checked,
        game_coop: (document.querySelector("#coop") as HTMLInputElement).checked,
        game_arcade: (document.querySelector("#arcade") as HTMLInputElement).checked,
        game_include_games_with_ai: (document.querySelector("#games-with-ai") as HTMLInputElement).checked,
        game_include_games_resumed_from_replay: (document.querySelector("#resume-from-replay") as HTMLInputElement).checked,
        expansion_wol: (document.querySelector("#expansion_wol") as HTMLInputElement).checked,
        expansion_hots: (document.querySelector("#expansion_hots") as HTMLInputElement).checked,
        expansion_lotv: (document.querySelector("#expansion_lotv") as HTMLInputElement).checked,
        server_americas: (document.querySelector("#server_americas") as HTMLInputElement).checked,
        server_europe: (document.querySelector("#server_europe") as HTMLInputElement).checked,
        server_asia: (document.querySelector("#server_asia") as HTMLInputElement).checked,
        player_name_must_include: (document.querySelector("#player_names_include") as HTMLInputElement).value,
        player_name_must_exclude: (document.querySelector("#player_names_exclude") as HTMLInputElement).value,
        date_played_min: Number((document.querySelector("#date_min") as HTMLInputElement).value),
        date_played_max: Number((document.querySelector("#date_max") as HTMLInputElement).value),
        game_duration_min: Number((document.querySelector("#duration_min") as HTMLInputElement).value),
        game_duration_max: Number((document.querySelector("#duration_max") as HTMLInputElement).value),
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
}

const get_replay_name_from_template = (template: string, replay: ReplayData): string => {
    // TODO
    return ""
}

const prevent_defaults = (e: Event) => {
    e.preventDefault();
    e.stopPropagation();
};

const init_drop_zone = () => {
    if (!drop_zone || !file_input) {
        console.error('Required elements not found');
        return
    }
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(event_name => {
        document.body.addEventListener(event_name, prevent_defaults, false);
    });

    // Highlight drop zone when dragging files over
    ['dragenter', 'dragover'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault();
            drop_zone.classList.add('border-blue-500', 'bg-blue-100');
        }, false);
    });

    ['dragleave', 'drop'].forEach(event_name => {
        drop_zone.addEventListener(event_name, (e) => {
            e.preventDefault();
            drop_zone.classList.remove('border-blue-500', 'bg-blue-100');
        }, false);
    });

    // Handle dropped files
    drop_zone.addEventListener('drop', async (e: DragEvent) => {
        e.preventDefault();

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
            console.log('File:', file.name, 'MD5:', md5)
        }

        // Add files to input element
        const data_transfer = new DataTransfer()
        for (const file of FILES) {
            data_transfer.items.add(file.file)
        }
        file_input.files = data_transfer.files
    });

    // TODO Display how many replays currently pass the filter
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
    for (const file_data of [...FILES]) {
        if (file_data.status !== 'uploaded') continue

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
}

const main = (): void => {
    init_drop_zone()
    console.log("Replay pack builder initialized")
    setInterval(process_files, 1000)
}

main()