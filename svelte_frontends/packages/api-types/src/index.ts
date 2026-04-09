import type { components, operations } from "./api.js"

export type { components, operations } from "./api.js"

export type VoiceOption = components["schemas"]["VoiceOption"]
export type QueueChapterRequest = components["schemas"]["QueueChapterRequest"]
export type HTTPValidationError = components["schemas"]["HTTPValidationError"]
export type ValidationError = components["schemas"]["ValidationError"]
export type BookListItem =
    operations["list_books_api_audiobook_books_get"]["responses"]["200"]["content"]["application/json"]
