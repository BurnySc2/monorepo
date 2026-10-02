import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

export const SearchFiltersSchema = z.object({
    search_text: z.string().default(""),
    channel_name: z.string().default(""),
    datetime_min: z.string().default(""),
    datetime_max: z.string().default(""),
    reactions_min: z.number().default(0),
    reactions_max: z.number().default(0),
    comments_min: z.number().default(0),
    comments_max: z.number().default(0),
    must_have_file: z.boolean().default(false),
    file_extension: z.string().default(""),
    file_duration_min: z.string().default("00:00:00"),
    file_duration_max: z.string().default("00:00:00"),
    file_size_min: z.number().default(0),
    file_size_max: z.number().default(0),
    file_image_width_min: z.number().default(0),
    file_image_width_max: z.number().default(0),
    file_image_height_min: z.number().default(0),
    file_image_height_max: z.number().default(0),
})

export type SearchFilters = z.infer<typeof SearchFiltersSchema>

const STORAGE_KEY = "search_filters"

const persisted = create_persisted_state(STORAGE_KEY, SearchFiltersSchema, SearchFiltersSchema.parse({}))

export const search_filters = persisted.state

export const is_loading = persisted.is_loading

export function reset_filters(): void {
    persisted.reset()
}
