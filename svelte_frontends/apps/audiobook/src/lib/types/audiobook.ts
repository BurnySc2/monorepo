// Types for Audiobook feature - mirrors backend models
// These will be replaced with generated types from OpenAPI when backend is running

export interface AudioSettings {
    voice: string
    rate: number
    volume: number
    pitch: number
}

export interface AudiobookBook {
    id: number
    uploaded_by: string
    book_title: string
    book_author: string
    custom_book_title: string
    custom_book_author: string
    chapter_count: number
    upload_date: string
}

export interface AudiobookChapter {
    id: number
    book: number
    chapter_title: string
    chapter_number: number
    word_count: number
    sentence_count: number
    queued: string | null
    started_converting: string | null
    minio_object_name: string | null
    audio_settings: string | null
}

export interface AudiobookChapterQueryResult {
    id: number
    book_id: number
    number_in_queue: number | null
    is_converting: boolean
    has_audio: boolean
    chapter_title: string
    chapter_number: number
    sentence_count: number
    minio_object_name: string | null
    minio_presigned_url: string
}

export interface BookWithChapters {
    book: AudiobookBook
    chapters: AudiobookChapterQueryResult[]
    available_voices: string[]
}
