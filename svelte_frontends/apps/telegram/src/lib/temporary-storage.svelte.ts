import type { components } from "@repo/api-types"
import { z } from "zod"

type ChannelStatsItem = components["schemas"]["ChannelStatsItem"]

const ChannelStatsItemSchema = z.custom<ChannelStatsItem>()

const TempStateSchema = z.object({
    channels: z.object({
        stats: z.array(ChannelStatsItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
    messages: z.object({
        results: z.array(ChannelStatsItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
    files: z.object({
        list: z.array(ChannelStatsItemSchema).nullable(),
        is_loading: z.boolean(),
        error: z.string().nullable(),
    }),
})

export type TTempState = z.infer<typeof TempStateSchema>

export const temp_state: TTempState = $state({
    channels: {
        stats: null,
        is_loading: false,
        error: null,
    },
    messages: {
        results: null,
        is_loading: false,
        error: null,
    },
    files: {
        list: null,
        is_loading: false,
        error: null,
    },
})
