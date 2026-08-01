<script lang="ts">
import { fetch_delete_file, fetch_queue_file, fetch_view_file } from "$lib/api"
import { is_loading as columns_loading } from "$lib/column_settings.svelte"
import ChannelsTab from "$lib/components/ChannelsTab.svelte"
import ColumnReorderDialog from "$lib/components/ColumnReorderDialog.svelte"
import FilesTab from "$lib/components/FilesTab.svelte"
import MediaDialog from "$lib/components/MediaDialog.svelte"
import MessagesTab from "$lib/components/MessagesTab.svelte"
import TabContainer from "$lib/components/TabContainer.svelte"
import { is_loading as file_columns_loading } from "$lib/file_column_settings.svelte"
import { is_loading as filters_loading } from "$lib/search_filters.svelte"
import { is_loading as sort_loading } from "$lib/sort_settings.svelte"
import { temp_state } from "$lib/temporary-storage.svelte"

let is_ready = $derived(
    !filters_loading.value && !sort_loading.value && !columns_loading.value && !file_columns_loading.value,
)

const tabs = [
    { id: "messages", label: "Messages" },
    { id: "files", label: "Files" },
    { id: "channels", label: "Channels" },
]

let active_tab: "messages" | "files" | "channels" = $state("messages")
let show_column_dialog = $state(false)
let show_media_dialog = $state(false)
let media_url = $state("")
let media_mime = $state("")

async function handle_queue_file(id: string) {
    await fetch_queue_file(id)
}

async function handle_delete_file(id: string) {
    try {
        await fetch_delete_file(id)
        temp_state.files.list = temp_state.files.list?.filter((file) => file.message_id.toString() !== id) ?? null
    } catch (e) {
        console.error("Delete file failed", e)
    }
}

async function handle_view_file(id: string) {
    try {
        const data = await fetch_view_file(id)
        if (data) {
            media_url = data.minio_url
            media_mime = data.mime_type
            show_media_dialog = true
        }
    } catch (e) {
        console.error("View file failed", e)
    }
}

function close_media_dialog() {
    show_media_dialog = false
    media_url = ""
    media_mime = ""
}
</script>

<main class="flex h-full flex-col items-center rounded-xl bg-gray-300">
    <div class="m-2 flex h-full flex-col gap-4 rounded-xl">
        <div class="flex gap-2">
            {#if active_tab !== "channels"}
                <button
                    class="h-full rounded-xl border-2 border-black p-2 hover:bg-yellow-500"
                    type="button"
                    onclick={() => (show_column_dialog = true)}
                >
                    Column order
                </button>
            {/if}
        </div>

        <TabContainer
            {tabs}
            bind:active_tab
        >
            {#if !is_ready}
                <div class="flex items-center justify-center p-8">
                    <div class="h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500"></div>
                </div>
            {:else if active_tab === "messages"}
                <MessagesTab
                    onqueue={handle_queue_file}
                    ondelete={handle_delete_file}
                    onview={handle_view_file}
                />
            {:else if active_tab === "channels"}
                <ChannelsTab />
            {:else}
                <FilesTab
                    onview={handle_view_file}
                    ondelete={handle_delete_file}
                />
            {/if}
        </TabContainer>
    </div>
</main>

{#if show_column_dialog && active_tab !== "channels"}
    <ColumnReorderDialog
        onclose={() => (show_column_dialog = false)}
        column_settings_type={active_tab}
    />
{/if}

{#if show_media_dialog}
    <MediaDialog
        url={media_url}
        mime_type={media_mime}
        onclose={close_media_dialog}
    />
{/if}
