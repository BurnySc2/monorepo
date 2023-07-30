<script lang="ts">
    import Dropzone from "svelte-file-dropzone/Dropzone.svelte"

    import { onMount } from "svelte"
    import { FFmpeg } from "@ffmpeg/ffmpeg"
    import { fetchFile, toBlobURL } from "@ffmpeg/util"

    let videoFile: string | Blob | undefined = undefined
    let subFile: string | Blob | undefined = undefined

    let resultUrl: string | undefined = undefined
    let resultName: string | undefined = undefined
    let resultProgress = 0

    $: command = ["-i", "input.mp4", "-vf", "subtitles=subtitle.srt", "output.mp4"]
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
        e.detail.acceptedFiles.forEach((file) => {
            if (file.name.endsWith(".srt")) {
                subFile = file
            } else {
                videoFile = file
            }
        })
    }

    async function convert() {
        resultName = videoFile.name
        resultProgress = 0
        ffmpeg.on("progress", ({ progress }) => {
            // between 0 and 1
            resultProgress = progress
        })
        await ffmpeg.writeFile("input.mp4", await fetchFile(videoFile))
        await ffmpeg.writeFile("subtitle.srt", await fetchFile(subFile))
        await ffmpeg.exec(command)
        const data = await ffmpeg.readFile("output.mp4")
        resultUrl = URL.createObjectURL(new Blob([data.buffer], { type: "video/mp4" }))
    }
</script>

<body>
    <section>
        {#if videoFile === undefined || subFile === undefined}
            <Dropzone on:drop={handleFilesSelect} />
        {/if}
        {#if videoFile !== undefined}
            <span>
                Input video file: {videoFile.name}
            </span>
        {/if}
        {#if subFile !== undefined}
            <span>
                Input subtitle file: {subFile.name}
            </span>
        {/if}
        {#if videoFile !== undefined && subFile !== undefined}
            {#if resultName === undefined}
                <!-- Uploaded -->
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
