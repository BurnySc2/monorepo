<script lang="ts">
interface Props {
    label?: string
    on_upload: (files: FileList) => void
    disabled?: boolean
}

let { label = "Select folder...", on_upload, disabled = false }: Props = $props()

async function handle_click() {
    if (disabled) {
        return
    }

    try {
        // @ts-expect-error showDirectoryPicker is not yet in TypeScript libs
        const dirHandle = await window.showDirectoryPicker()
        const files = await collect_sc2replay_files(dirHandle)
        if (files.length > 0) {
            on_upload(files)
        }
    } catch (err) {
        if ((err as Error).name !== "AbortError") {
            console.error("Error selecting folder:", err)
        }
    }
}

async function collect_sc2replay_files(dirHandle: FileSystemDirectoryHandle): Promise<FileList> {
    const valid_files: File[] = []

    async function walkDir(handle: FileSystemDirectoryHandle) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        for await (const entry of (handle as any).values()) {
            if (entry.kind === "file" && entry.name.endsWith(".SC2Replay")) {
                const file = await entry.getFile()
                valid_files.push(file)
            } else if (entry.kind === "directory") {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                await walkDir(entry as any)
            }
        }
    }

    await walkDir(dirHandle)

    const dt = new DataTransfer()
    for (const file of valid_files) {
        dt.items.add(file)
    }
    return dt.files
}
</script>

<button
    class="btn-secondary"
    onclick={handle_click}
    {disabled}
>
    📁 {label}
</button>
