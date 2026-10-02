import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

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

const persisted = create_persisted_state(STORAGE_KEY, ColumnSettingsSchema, ColumnSettingsSchema.parse({}))

export const column_settings = persisted.state
export const is_loading = persisted.is_loading
