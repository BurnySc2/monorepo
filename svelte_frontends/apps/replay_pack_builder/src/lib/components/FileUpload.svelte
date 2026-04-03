<script lang="ts">
let { is_processing, on_upload }: { is_processing: boolean; on_upload: (files: FileList) => void } = $props()

let is_dragging = $state(false)
let file_input: HTMLInputElement | undefined = $state()

function handle_drag_over(event: DragEvent) {
    event.preventDefault()
    if (!is_processing) {
        is_dragging = true
    }
}

function handle_drag_leave() {
    is_dragging = false
}

function handle_drop(event: DragEvent) {
    event.preventDefault()
    is_dragging = false
    if (is_processing || !event.dataTransfer?.files) {
        return
    }
    process_files(event.dataTransfer.files)
}

function handle_click() {
    if (!is_processing && file_input) {
        file_input.click()
    }
}

function handle_change() {
    if (file_input?.files) {
        process_files(file_input.files)
    }
}

function process_files(files: FileList) {
    const valid_files = Array.from(files).filter((file) => file.name.endsWith(".SC2Replay"))
    if (valid_files.length > 0) {
        const data_transfer = new DataTransfer()
        for (const file of valid_files) {
            data_transfer.items.add(file)
        }
        on_upload(data_transfer.files)
    }
}
</script>

<div
    class="drop-zone"
    class:dragging={is_dragging}
    class:disabled={is_processing}
    role="button"
    tabindex="0"
    ondragover={handle_drag_over}
    ondragleave={handle_drag_leave}
    ondrop={handle_drop}
    onclick={handle_click}
    onkeydown={(e) => e.key === "Enter" && handle_click()}
>
    <input
        type="file"
        accept=".SC2Replay"
        multiple
        bind:this={file_input}
        onchange={handle_change}
        disabled={is_processing}
        class="hidden-input"
    >
    <div class="drop-zone-icon">📁</div>
    {#if is_processing}
        <p class="drop-zone-text">Processing...</p>
    {:else}
        <p class="drop-zone-text">Drag & drop .SC2Replay files here</p>
        <p class="drop-zone-hint">or click to browse</p>
    {/if}
</div>