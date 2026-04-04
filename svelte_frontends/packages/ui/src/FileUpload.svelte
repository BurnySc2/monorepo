<script lang="ts">
interface Props {
    label: string
    on_upload: (files: FileList) => void
    disabled?: boolean
    accept?: string
}

let { label, on_upload, disabled = false, accept = "" }: Props = $props()

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

function filter_files(files: FileList): FileList {
    if (!accept) {
        return files
    }
    const ext = accept.replace(".", "")
    const valid_files = Array.from(files).filter((file) => file.name.endsWith(`.${ext}`))
    if (valid_files.length === 0) {
        return files
    }
    const dt = new DataTransfer()
    for (const file of valid_files) {
        dt.items.add(file)
    }
    return dt.files
}

function handle_drop(e: DragEvent) {
    e.preventDefault()
    is_dragging = false
    if (disabled) {
        return
    }

    const files = e.dataTransfer?.files
    if (files && files.length > 0) {
        on_upload(filter_files(files))
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
        on_upload(filter_files(files))
    }
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
        accept={accept || undefined}
        onchange={handle_file_change}
    >
</div>
