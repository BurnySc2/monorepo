<script lang="ts">
    import Dropzone from "svelte-file-dropzone/Dropzone.svelte"

    import { onMount } from "svelte"
    import { FFmpeg } from "@ffmpeg/ffmpeg"
    import { fetchFile, toBlobURL } from "@ffmpeg/util"

    let file: string | Blob | undefined = undefined
    let crfValue = 23

    let resultUrl: string | undefined = undefined
    let resultName: string | undefined = undefined
    let resultProgress = 0

    $: command = [
        "-i",
        "input.mp4",
        "output.mp4",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        // "medium",
        "-crf",
        String(crfValue),
        "-acodec",
        "mp3",
        "-scodec",
        "copy",
        "-map",
        "0",
    ]
    $: commandString = command.join(" ")

    let ffmpeg: FFmpeg | null = null

    onMount(async () => {
        await load()
    })

    const load = async () => {
        ffmpeg = new FFmpeg()
        const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.1/dist/esm"
        console.log("Loading")
        ffmpeg.on("log", ({ message }) => {
            console.log(message)
        })
        await ffmpeg.load({
            coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, "text/javascript"),
            wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, "application/wasm"),
            // workerURL: await toBlobURL(`${baseURL}/ffmpeg-core.worker.js`, "text/javascript"),
            // SharedArrayBuffer is not defined
            // thread: true,
        })
        console.log("Loaded")
    }

    function handleFilesSelect(e) {
        file = e.detail.acceptedFiles[0]
    }

    async function convert() {
        resultName = file.name
        resultProgress = 0
        ffmpeg.on("progress", ({ progress }) => {
            // between 0 and 1
            resultProgress = progress
        })
        await ffmpeg.writeFile("input.mp4", await fetchFile(file))
        await ffmpeg.exec(command)
        const data = await ffmpeg.readFile("output.mp4")
        resultUrl = URL.createObjectURL(new Blob([data.buffer], { type: "video/mp4" }))
    }
</script>

<body>
    <section>
        {#if file === undefined}
            <Dropzone on:drop={handleFilesSelect} />
        {:else}
            <!-- <button
                    on:click={() => {
                        file = undefined
                    }}>Delete</button
                > -->
            <!-- <a href={URL.createObjectURL(file)} download={file.name}>Download original</a> -->
            <span>
                Input: {file.name}
            </span>
            {#if resultName === undefined}
                <!-- Uploaded -->
                <label>
                    <input type="number" bind:value={crfValue} min="10" max="50" step="1" />
                    CRF
                </label>
                <button on:click={convert}>Convert</button>
                <input type="text" value={"ffmpeg " + commandString} readonly size={commandString.length} />
            {:else if resultUrl === undefined}
                <!-- Converting -->
                <progress value={resultProgress} />
            {:else}
                <!-- Done -->
                <a href={resultUrl} download={resultName}>Download result</a>
            {/if}
            {#if resultName !== undefined}
                <label>
                    Output file name:
                    <input type="text" placeholder="Rename me" bind:value={resultName} />
                </label>
            {/if}
        {/if}
    </section>
</body>

<style>
    body > section {
        display: flex;
        flex-direction: column;
        gap: 10px;
        justify-content: center;
        align-items: center;
    }
</style>
