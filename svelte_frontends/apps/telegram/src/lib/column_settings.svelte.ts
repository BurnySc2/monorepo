import { z } from "zod"
import { browser } from "$app/environment"

export const ColumnSchema = z.object({
    key: z.string(),
    name: z.string(),
})

export type Column = z.infer<typeof ColumnSchema>

export const ColumnSettingsSchema = z.object({
    active_columns: z.array(ColumnSchema).default([
        { key: "message_date", name: "Date" },
        { key: "channel_title", name: "Channel" },
        { key: "message_text", name: "Message" },
        { key: "amount_of_reactions", name: "Reactions" },
        { key: "amount_of_comments", name: "Comments" },
        { key: "file_extension", name: "Ext" },
        { key: "file_size_bytes", name: "Size" },
        { key: "file_duration_seconds", name: "Duration" },
        { key: "message_link", name: "Link" },
    ]),
    disabled_columns: z.array(ColumnSchema).default([
        { key: "views", name: "Views" },
        { key: "forwards", name: "Forwards" },
    ]),
})

export type ColumnSettings = z.infer<typeof ColumnSettingsSchema>

const STORAGE_KEY = "column_settings"

export const column_settings = $state<ColumnSettings>(ColumnSettingsSchema.parse({}))
export const is_loading = $state({ value: true })

$effect.root(() => {
    $effect(() => {
        if (browser) {
            if (is_loading.value) {
                is_loading.value = false
                const data = localStorage.getItem(STORAGE_KEY)
                if (data !== null) {
                    Object.assign(column_settings, ColumnSettingsSchema.parse(JSON.parse(data)))
                }
            } else {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(column_settings))
            }
        }

        $state.snapshot(column_settings)
    })
})
