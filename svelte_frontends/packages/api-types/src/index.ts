import type { components, operations } from "./api.js"

export type { components, operations } from "./api.js"

export type VoiceOption = components["schemas"]["VoiceOption"]
export type QueueChapterRequest = components["schemas"]["QueueChapterRequest"]
export type HTTPValidationError = components["schemas"]["HTTPValidationError"]
export type ValidationError = components["schemas"]["ValidationError"]
export type BookListItem =
    operations["list_books_api_audiobook_books_get"]["responses"]["200"]["content"]["application/json"]
export type BookListItemSchema = components["schemas"]["BookListItem"]
export type ChapterDetail = components["schemas"]["ChapterDetail"]
export type BookWithChapters = components["schemas"]["BookWithChapters"]
export type DeleteResponse = components["schemas"]["DeleteResponse"]
export type QueueResponse = components["schemas"]["QueueResponse"]
export type ParsedReplayFile = components["schemas"]["ParsedReplayFile"]
export type ReplayPlayer = components["schemas"]["ReplayPlayer"]
export type ReplayTeam = components["schemas"]["ReplayTeam"]
export type ParseReplayResponse =
    operations["parse_replay_file_api_parse_replay_post"]["responses"]["200"]["content"]["application/json"]
