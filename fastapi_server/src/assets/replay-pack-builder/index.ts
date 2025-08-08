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
    team_victory: number
    map_name: string
    date_played: string
    date_time_played: string
    game_duration: number
    region: "Americas" | "Europe" | "Asia"
    region_short: "NA" | "EU" | "KR"
}

let FILES: FileData[] = []
let PARSED: ReplayData[] = []

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

const prevent_defaults = (e: Event) => {
    e.preventDefault();
    e.stopPropagation();
};

if (!drop_zone || !file_input) {
    console.error('Required elements not found');
} else {
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

    // TODO After drag drop, parse the file (extract file name, calculate md5 to get a unique id per replay to not upload same replay twice)

    // TODO For each replay, parse data with the help of backend, extract metadata (player name, map name, date played, mmr etc)

    // TODO Display how many replays currently pass the filter

    // TODO When clicking "build and download pack", zip selected files in frontend and download zip with renamed files
}

const main = (): void => {
    console.log("Replay pack builder initialized");
};
