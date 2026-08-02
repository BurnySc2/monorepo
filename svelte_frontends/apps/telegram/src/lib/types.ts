export interface SearchFilters {
    search_text: string
    channel_name: string
    datetime_min: string
    datetime_max: string
    reactions_min: number
    reactions_max: number
    comments_min: number
    comments_max: number
    must_have_file: boolean
    file_extension: string
    file_duration_min: string
    file_duration_max: string
    file_size_min: number
    file_size_max: number
    file_image_width_min: number
    file_image_width_max: number
    file_image_height_min: number
    file_image_height_max: number
}
