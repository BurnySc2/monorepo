<script lang="ts">
import { fetch_delete_file, fetch_queue_file, fetch_view_file } from "$lib/api"
import ColumnReorderDialog from "$lib/components/ColumnReorderDialog.svelte"
import FilesTab from "$lib/components/FilesTab.svelte"
import MediaDialog from "$lib/components/MediaDialog.svelte"
import MessagesTab from "$lib/components/MessagesTab.svelte"
import TabContainer from "$lib/components/TabContainer.svelte"

const tabs = [
    { id: "messages", label: "Messages" },
    { id: "files", label: "Files" },
]

let active_tab: "messages" | "files" = $state("messages")
let show_column_dialog = $state(false)
let show_media_dialog = $state(false)
let media_url = $state("")
let media_mime = $state("")

async function handle_queue_file(id: string) {
    try {
        await fetch_queue_file(id)
    } catch (e) {
        console.error("Queue file failed", e)
    }
}

async function handle_delete_file(id: string) {
    try {
        await fetch_delete_file(id)
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
            <button
                class="h-full rounded-xl border-2 border-black p-2 hover:bg-yellow-500"
                type="button"
                onclick={() => (show_column_dialog = true)}
            >
                Column order
            </button>
        </div>

        <TabContainer
            {tabs}
            bind:active_tab
        >
            {#if active_tab === "messages"}
                <MessagesTab
                    onqueue={handle_queue_file}
                    ondelete={handle_delete_file}
                    onview={handle_view_file}
                />
            {:else}
                <FilesTab
                    onview={handle_view_file}
                    ondelete={handle_delete_file}
                />
            {/if}
        </TabContainer>
    </div>
</main>

{#if show_column_dialog}
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
