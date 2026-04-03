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
    class="upload-zone"
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
    <div class="upload-content">
        <div class="upload-icon">📁</div>
        {#if is_processing}
            <p class="upload-text">Processing...</p>
        {:else}
            <p class="upload-text">Drag & drop .SC2Replay files here</p>
            <p class="upload-hint">or click to browse</p>
        {/if}
    </div>
</div>

<style>
.upload-zone {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 32px;
    text-align: center;
    cursor: pointer;
    transition:
        border-color 0.2s,
        background-color 0.2s;
}

.upload-zone:hover:not(.disabled) {
    border-color: #666;
    background-color: #f9f9f9;
}

.upload-zone.dragging {
    border-color: #2196f3;
    background-color: #e3f2fd;
}

.upload-zone.disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.hidden-input {
    display: none;
}

.upload-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
}

.upload-icon {
    font-size: 48px;
}

.upload-text {
    margin: 0;
    font-size: 16px;
    color: #333;
}

.upload-hint {
    margin: 0;
    font-size: 14px;
    color: #888;
}
</style>
