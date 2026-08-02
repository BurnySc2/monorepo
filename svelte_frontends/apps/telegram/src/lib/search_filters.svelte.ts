import { z } from "zod"
import { browser } from "$app/environment"

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

export const search_filters = $state<SearchFilters>(SearchFiltersSchema.parse({}))

export const is_loading = $state({ value: true })

$effect.root(() => {
    $effect(() => {
        if (browser) {
            if (is_loading.value) {
                is_loading.value = false
                const data = localStorage.getItem(STORAGE_KEY)
                if (data !== null) {
                    Object.assign(search_filters, SearchFiltersSchema.parse(JSON.parse(data)))
                }
            } else {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(search_filters))
            }
        }

        $state.snapshot(search_filters)
    })
})

export function reset_filters(): void {
    Object.assign(search_filters, SearchFiltersSchema.parse({}))
}
