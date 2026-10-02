import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

export const ColumnSchema = z.object({
    key: z.string(),
    name: z.string(),
})

export type Column = z.infer<typeof ColumnSchema>

export const FileColumnSettingsSchema = z.object({
    active_columns: z.array(ColumnSchema).default([
        { key: "message_date", name: "Date" },
        { key: "channel_title", name: "Channel" },
        { key: "file_extension", name: "Ext" },
        { key: "file_size_bytes", name: "Size" },
        { key: "file_duration_seconds", name: "Duration" },
        { key: "file_mime_type", name: "MIME" },
        { key: "message_text", name: "Message" },
        { key: "message_link", name: "Link" },
    ]),
    disabled_columns: z.array(ColumnSchema).default([
        { key: "download_queue_time", name: "Queued" },
        { key: "download_start_time", name: "Download Start" },
        { key: "download_finished_time", name: "Download Finished" },
        { key: "download_retry_attempt", name: "Retry # " },
        { key: "s3_object_name", name: "S3 Name" },
        { key: "message_id", name: "Message ID" },
        { key: "status", name: "Status" },
        { key: "channel_username", name: "Username" },
    ]),
})

export type FileColumnSettings = z.infer<typeof FileColumnSettingsSchema>

const STORAGE_KEY = "file_column_settings"

const persisted = create_persisted_state(STORAGE_KEY, FileColumnSettingsSchema, FileColumnSettingsSchema.parse({}))

export const file_column_settings = persisted.state
export const is_loading = persisted.is_loading
