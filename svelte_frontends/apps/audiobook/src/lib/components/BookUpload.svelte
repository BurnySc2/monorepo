<script lang="ts">
    import Spinner from "./Spinner.svelte"

interface Props {
    on_upload: (file: File) => Promise<void>
    is_uploading?: boolean
    disabled?: boolean
}

let { on_upload, is_uploading = false, disabled = false }: Props = $props()

let is_dragging = $state(false)

function handle_drag_over(event: DragEvent) {
    event.preventDefault()
    if (!disabled) {
        is_dragging = true
    }
}

function handle_drag_leave(event: DragEvent) {
    event.preventDefault()
    is_dragging = false
}

async function handle_drop(event: DragEvent) {
    event.preventDefault()
    is_dragging = false

    if (disabled) {
        return
    }

    const files = event.dataTransfer?.files
    if (!files || files.length === 0) {
        return
    }

    const file = files[0]
    if (!file.name.endsWith(".epub")) {
        alert("Please drop an .epub file")
        return
    }

    await on_upload(file)
}

async function handle_click() {
    if (disabled || is_uploading) {
        return
    }

    const input = document.createElement("input")
    input.type = "file"
    input.accept = ".epub"
    input.onchange = async (e) => {
        const target = e.target as HTMLInputElement
        const file = target.files?.[0]
        if (file) {
            await on_upload(file)
        }
    }
    input.click()
}
</script>

<div
    class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200
        {is_dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
        {disabled || is_uploading ? "opacity-50 cursor-not-allowed" : ""}"
    ondrop={handle_drop}
    ondragover={handle_drag_over}
    ondragleave={handle_drag_leave}
    onclick={handle_click}
    role="button"
    tabindex="0"
    onkeydown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
            handle_click()
        }
    }}
>
    {#if is_uploading}
        <Spinner size="lg" />
        <p class="mt-4 text-gray-600">Processing book...</p>
    {:else}
        <svg
            class="w-12 h-12 mx-auto text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            ></path>
        </svg>
        <p class="mt-4 text-gray-600">Drop your .epub book here to upload</p>
        <p class="mt-2 text-sm text-gray-400">or click to browse</p>
    {/if}
</div>
