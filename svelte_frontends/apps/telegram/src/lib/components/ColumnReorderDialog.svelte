<script lang="ts">
interface Props {
    onclose: () => void
}

let { onclose }: Props = $props()

interface Column {
    key: string
    name: string
}

let active_columns = $state<Column[]>([
    { key: "message_date", name: "Date" },
    { key: "channel_title", name: "Channel" },
    { key: "message_text", name: "Message" },
    { key: "amount_of_reactions", name: "Reactions" },
    { key: "amount_of_comments", name: "Comments" },
    { key: "file_extension", name: "Ext" },
    { key: "file_size_bytes", name: "Size" },
    { key: "file_duration_seconds", name: "Duration" },
    { key: "message_link", name: "Link" },
])

let disabled_columns = $state<Column[]>([
    { key: "views", name: "Views" },
    { key: "forwards", name: "Forwards" },
])

let dragging_item: Column | null = $state(null)

function handle_drag_start(column: Column) {
    dragging_item = column
}

function handle_drag_end() {
    dragging_item = null
}

function handle_drag_over(event: DragEvent, target_column: Column, target_list: "active" | "disabled") {
    event.preventDefault()
    if (!dragging_item) {
        return
    }

    // Remove from current list
    if (active_columns.find((c) => c.key === dragging_item?.key)) {
        active_columns = active_columns.filter((c) => c.key !== dragging_item?.key)
    } else {
        disabled_columns = disabled_columns.filter((c) => c.key !== dragging_item?.key)
    }

    // Find insert position
    const target_list_ref = target_list === "active" ? active_columns : disabled_columns
    const insert_index = target_list_ref.findIndex((c) => c.key === target_column.key)

    // Insert at position
    if (insert_index >= 0) {
        if (target_list === "active") {
            active_columns = [
                ...active_columns.slice(0, insert_index),
                dragging_item,
                ...active_columns.slice(insert_index),
            ]
        } else {
            disabled_columns = [
                ...disabled_columns.slice(0, insert_index),
                dragging_item,
                ...disabled_columns.slice(insert_index),
            ]
        }
    } else {
        // Append to end
        if (target_list === "active") {
            active_columns = [...active_columns, dragging_item]
        } else {
            disabled_columns = [...disabled_columns, dragging_item]
        }
    }
}

function handle_drop_to_empty(target_list: "active" | "disabled") {
    if (!dragging_item) {
        return
    }

    // Remove from current list
    active_columns = active_columns.filter((c) => c.key !== dragging_item?.key)
    disabled_columns = disabled_columns.filter((c) => c.key !== dragging_item?.key)

    // Add to target list
    if (target_list === "active") {
        active_columns = [...active_columns, dragging_item]
    } else {
        disabled_columns = [...disabled_columns, dragging_item]
    }
}

async function handle_save() {
    try {
        const columns_order = active_columns.map((c) => c.key).join(";")
        await fetch("/telegram-browser/save-active-columns", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ "columns-order": columns_order }),
        })
        onclose()
    } catch (e) {
        console.error("Failed to save columns", e)
    }
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
    role="dialog"
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
                            ondrop={() => handle_drop_to_empty("active")}
                        >
                            {#each active_columns as column (column.key)}
                                <div
                                    id={column.key}
                                    class="draggable-item whitespace-nowrap rounded-xl border border-black p-2 hover:bg-yellow-300"
                                    draggable="true"
                                    role="option"
                                    tabindex="0"
                                    ondragstart={() => handle_drag_start(column)}
                                    ondragend={handle_drag_end}
                                    ondragover={(e) => handle_drag_over(e, column, "active")}
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
                            ondrop={() => handle_drop_to_empty("disabled")}
                        >
                            {#each disabled_columns as column (column.key)}
                                <div
                                    id={column.key}
                                    class="draggable-item whitespace-nowrap rounded-xl border border-black p-2 hover:bg-yellow-300"
                                    draggable="true"
                                    role="option"
                                    tabindex="0"
                                    ondragstart={() => handle_drag_start(column)}
                                    ondragend={handle_drag_end}
                                    ondragover={(e) => handle_drag_over(e, column, "disabled")}
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
