<script lang="ts">
import { IconUpload, Spinner, toast } from "@repo/ui"

// SPEC.md section 11 names this PdfUpload.svelte; this file is BookUpload.svelte
// cloned from apps/audiobook (accept filter + drop handler adapted to .pdf).
// TODO(@documenter): reconcile SPEC section 11 file list with this clone.

interface Props {
    on_upload: (file: File) => Promise<void>
    is_uploading?: boolean
    disabled?: boolean
}

let { on_upload, is_uploading = false, disabled = false }: Props = $props()

let is_dragging = $state(false)

let container_class = $derived(
    `border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${is_dragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"} ${disabled || is_uploading ? "opacity-50 cursor-not-allowed" : ""}`,
)

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
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        toast.error("Please drop a .pdf file")
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
    input.accept = ".pdf"
    input.onchange = async (e) => {
        const target = e.target as HTMLInputElement
        const file = target.files?.[0]
        if (file) {
            if (!file.name.toLowerCase().endsWith(".pdf")) {
                toast.error("Please select a .pdf file")
                return
            }
            await on_upload(file)
        }
    }
    input.click()
}
</script>

<div
    class={container_class}
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
        <Spinner />
        <p class="mt-4 text-gray-600">Processing PDF...</p>
    {:else}
        <IconUpload class="h-12 w-12 mx-auto text-gray-400" />
        <p class="mt-4 text-gray-600">Drop your .pdf book here to upload</p>
        <p class="mt-2 text-sm text-gray-400">or click to browse</p>
    {/if}
</div>
