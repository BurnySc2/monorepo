<script lang="ts">
import { Spinner } from "@repo/ui"

interface Props {
    label: string
    on_upload: (files: FileList) => void
    disabled?: boolean
}

let { label, on_upload, disabled = false }: Props = $props()

let is_dragging = $state(false)
let file_input: HTMLInputElement

function handle_dragover(e: DragEvent) {
    e.preventDefault()
    if (!disabled) {
        is_dragging = true
    }
}

function handle_dragleave() {
    is_dragging = false
}

function handle_drop(e: DragEvent) {
    e.preventDefault()
    is_dragging = false
    if (disabled) {
        return
    }

    const files = e.dataTransfer?.files
    if (files && files.length > 0) {
        on_upload(files)
    }
}

function handle_click() {
    if (!disabled) {
        file_input?.click()
    }
}

function handle_file_change(e: Event) {
    const target = e.target as HTMLInputElement
    const files = target.files
    if (files && files.length > 0) {
        on_upload(files)
    }
    // Reset input so same file can be selected again
    target.value = ""
}
</script>

<div
    class="drop-zone"
    class:dragging={is_dragging}
    class:disabled
    role="button"
    tabindex="0"
    ondragover={handle_dragover}
    ondragleave={handle_dragleave}
    ondrop={handle_drop}
    onclick={handle_click}
    onkeydown={(e) => e.key === "Enter" && handle_click()}
>
    <div class="drop-zone-icon">{disabled ? "⏳" : "📁"}</div>
    <p class="drop-zone-text">{label}</p>
    <p class="drop-zone-hint">or click to browse</p>
    <input
        bind:this={file_input}
        type="file"
        class="hidden-input"
        accept=".SC2Replay"
        onchange={handle_file_change}
    >
</div>
