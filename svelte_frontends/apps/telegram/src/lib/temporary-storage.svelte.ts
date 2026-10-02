import type { components } from "@repo/api-types"
import { create_loading_state } from "@repo/sc2-utils"
import { z } from "zod"

type ChannelStatsItem = components["schemas"]["ChannelStatsItem"]
type SearchResultItem = components["schemas"]["SearchResultItem"]
type DownloadedFileItem = components["schemas"]["DownloadedFileItem"]

const ChannelStatsItemSchema = z.custom<ChannelStatsItem>()
const SearchResultItemSchema = z.custom<SearchResultItem>()
const DownloadedFileItemSchema = z.custom<DownloadedFileItem>()

const TempStateSchema = z.object({
    channels: z.object({
        stats: z.array(ChannelStatsItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
    messages: z.object({
        results: z.array(SearchResultItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
    files: z.object({
        list: z.array(DownloadedFileItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
})

export type TTempState = z.infer<typeof TempStateSchema>

export const temp_state: TTempState = $state({
    channels: {
        stats: null,
        ...create_loading_state(false),
        error: null,
    },
    messages: {
        results: null,
        ...create_loading_state(false),
        error: null,
    },
    files: {
        list: null,
        ...create_loading_state(false),
        error: null,
    },
})
