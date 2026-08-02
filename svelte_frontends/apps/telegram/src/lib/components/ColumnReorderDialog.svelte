<script lang="ts">
import type { Column } from "$lib/column_settings.svelte"
import { column_settings } from "$lib/column_settings.svelte"
import { file_column_settings } from "$lib/file_column_settings.svelte"

interface Props {
    onclose: () => void
    column_settings_type: "messages" | "files"
}

let { onclose, column_settings_type }: Props = $props()

const active_settings = $derived(column_settings_type === "messages" ? column_settings : file_column_settings)

let dragging_item: Column | null = $state(null)
let drag_source_list: "active" | "disabled" | null = $state(null)

function handle_drag_start(column: Column, source_list: "active" | "disabled") {
    dragging_item = column
    drag_source_list = source_list
}

function handle_drag_end() {
    dragging_item = null
    drag_source_list = null
}

function handle_drop_on_item(event: DragEvent, target_column: Column, target_list: "active" | "disabled") {
    event.preventDefault()
    event.stopPropagation()

    if (!dragging_item || !drag_source_list) {
        return
    }

    // Get the target list and indices
    const target = target_list === "active" ? active_settings.active_columns : active_settings.disabled_columns
    const target_index = target.findIndex((c) => c.key === target_column.key)
    const source_index = target.findIndex((c) => c.key === dragging_item?.key)

    // Remove from source
    if (drag_source_list === "active") {
        active_settings.active_columns = active_settings.active_columns.filter((c) => c.key !== dragging_item?.key)
    } else {
        active_settings.disabled_columns = active_settings.disabled_columns.filter((c) => c.key !== dragging_item?.key)
    }

    // Get fresh target list after removal
    const fresh_target = target_list === "active" ? active_settings.active_columns : active_settings.disabled_columns

    // Adjust index for same-list reordering
    let insert_index = target_index
    if (drag_source_list === target_list && source_index < target_index) {
        // Item was before target, so target shifted down by 1 after removal
        insert_index -= 1
    }

    // Insert at adjusted position
    if (target_list === "active") {
        active_settings.active_columns = [
            ...fresh_target.slice(0, insert_index),
            dragging_item,
            ...fresh_target.slice(insert_index),
        ]
    } else {
        active_settings.disabled_columns = [
            ...fresh_target.slice(0, insert_index),
            dragging_item,
            ...fresh_target.slice(insert_index),
        ]
    }

    handle_drag_end()
}

function handle_drop_on_empty(event: DragEvent, target_list: "active" | "disabled") {
    event.preventDefault()

    if (!dragging_item || !drag_source_list) {
        return
    }

    // Remove from source
    if (drag_source_list === "active") {
        active_settings.active_columns = active_settings.active_columns.filter((c) => c.key !== dragging_item?.key)
    } else {
        active_settings.disabled_columns = active_settings.disabled_columns.filter((c) => c.key !== dragging_item?.key)
    }

    // Add to end of target
    if (target_list === "active") {
        active_settings.active_columns = [...active_settings.active_columns, dragging_item]
    } else {
        active_settings.disabled_columns = [...active_settings.disabled_columns, dragging_item]
    }

    handle_drag_end()
}

function handle_save() {
    onclose()
}

function handle_cancel() {
    onclose()
}

function handle_keydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
        handle_cancel()
    }
}
</script>

<svelte:window onkeydown={handle_keydown} />

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<dialog
    open
    class="fixed inset-0 z-50 flex h-full w-full items-center justify-center bg-black/30 backdrop-blur-sm"
    onclick={handle_cancel}
    aria-modal="true"
>
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="flex flex-col gap-4 rounded-xl bg-gray-100 p-8 ring-8"
        onclick={(e) => e.stopPropagation()}
    >
        <table class="h-1">
            <tbody>
                <tr>
                    <th>
                        <div>Active columns</div>
                    </th>
                    <th>
                        <div>Disabled columns</div>
                    </th>
                </tr>
                <tr>
                    <!-- Active columns -->
                    <td>
                        <div
                            id="active-columns"
                            class="droppable-container mx-2 flex h-64 w-48 flex-col gap-2 overflow-auto border border-black p-2"
                            role="listbox"
                            ondragover={(e) => e.preventDefault()}
                            ondrop={(e) => handle_drop_on_empty(e, "active")}
                        >
                            {#each active_settings.active_columns as column (column.key)}
                                <div
                                    id={column.key}
                                    class="draggable-item whitespace-nowrap rounded-xl border border-black p-2 hover:bg-yellow-300"
                                    draggable="true"
                                    role="option"
                                    tabindex="0"
                                    ondragstart={() => handle_drag_start(column, "active")}
                                    ondragend={handle_drag_end}
                                    ondragover={(e) => e.preventDefault()}
                                    ondrop={(e) => handle_drop_on_item(e, column, "active")}
                                >
                                    {column.name}
                                </div>
                            {/each}
                        </div>
                    </td>

                    <!-- Disabled columns -->
                    <td>
                        <div
                            id="disabled-columns"
                            class="droppable-container mx-2 flex h-64 w-48 flex-col gap-2 overflow-auto border border-black p-2"
                            role="listbox"
                            ondragover={(e) => e.preventDefault()}
                            ondrop={(e) => handle_drop_on_empty(e, "disabled")}
                        >
                            {#each active_settings.disabled_columns as column (column.key)}
                                <div
                                    id={column.key}
                                    class="draggable-item whitespace-nowrap rounded-xl border border-black p-2 hover:bg-yellow-300"
                                    draggable="true"
                                    role="option"
                                    tabindex="0"
                                    ondragstart={() => handle_drag_start(column, "disabled")}
                                    ondragend={handle_drag_end}
                                    ondragover={(e) => e.preventDefault()}
                                    ondrop={(e) => handle_drop_on_item(e, column, "disabled")}
                                >
                                    {column.name}
                                </div>
                            {/each}
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>

        <div class="flex gap-4">
            <button
                type="button"
                class="grow rounded-xl bg-green-400 p-2 hover:bg-green-500"
                onclick={handle_save}
            >
                Save changes
            </button>
            <button
                type="button"
                class="grow rounded-xl bg-red-400 p-2 hover:bg-red-500"
                onclick={handle_cancel}
            >
                Cancel
            </button>
        </div>
    </div>
</dialog>

<style>
.draggable-item {
    cursor: move;
}

.draggable-item:active {
    opacity: 0.5;
}
</style>
