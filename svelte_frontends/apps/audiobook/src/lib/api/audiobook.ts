// API service for Audiobook feature
import type {
    BookListItemSchema as AudiobookBook,
    ChapterDetail as AudiobookChapterQueryResult,
    QueueChapterRequest as AudioSettings,
    BookWithChapters,
    VoiceInfo,
} from "@repo/api-types"
import { mock_book_data } from "./mock_data"

const API_BASE_URL = import.meta.env?.VITE_API_TARGET || "http://localhost:8000"

const USE_MOCK = typeof import.meta.env !== "undefined" && import.meta.env.VITE_USE_MOCK === "true"

export async function get_books(): Promise<AudiobookBook[]> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books`, {
        credentials: "include",
    })
    if (!response.ok) {
        throw new Error("Failed to fetch books")
    }
    return response.json()
}

export async function get_book(book_id: number): Promise<BookWithChapters | null> {
    if (USE_MOCK) {
        console.log("[MOCK] get_book called, returning mock data")
        return mock_book_data
    }

    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}`, {
        credentials: "include",
    })
    if (response.status === 404) {
        return null
    }
    if (!response.ok) {
        throw new Error("Failed to fetch book")
    }
    return response.json()
}

export async function upload_epub(file: File): Promise<void> {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}/api/audiobook/upload`, {
        method: "POST",
        credentials: "include",
        body: formData,
    })

    if (!response.ok) {
        const error_data = await response.json().catch(() => ({}))
        throw new Error(error_data.detail || "Failed to upload book")
    }
}

export async function get_available_voices(): Promise<VoiceInfo[]> {
    const response = await fetch(`${API_BASE_URL}/tts-generate/voices`, {
        credentials: "include",
    })
    if (!response.ok) {
        throw new Error("Failed to fetch voices")
    }
    return response.json()
}

export async function update_book_title(book_id: number, title: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/title`, {
        method: "PUT",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ title }),
    })

    if (!response.ok) {
        throw new Error("Failed to update title")
    }
}

export async function update_book_author(book_id: number, author: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/author`, {
        method: "PUT",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ author }),
    })

    if (!response.ok) {
        throw new Error("Failed to update author")
    }
}

export async function queue_chapter_audio(
    book_id: number,
    chapter_id: number,
    audio_settings: AudioSettings,
): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/chapters/${chapter_id}/queue`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(audio_settings),
    })

    if (!response.ok) {
        throw new Error("Failed to queue chapter audio")
    }
}

export async function delete_chapter_audio(book_id: number, chapter_id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/chapters/${chapter_id}`, {
        method: "DELETE",
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to delete chapter audio")
    }
}

export async function queue_all_chapters(book_id: number, audio_settings: AudioSettings): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/queue-all`, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(audio_settings),
    })

    if (!response.ok) {
        throw new Error("Failed to queue all chapters")
    }
}

export async function delete_book(book_id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}`, {
        method: "DELETE",
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to delete book")
    }
}

export async function delete_all_audio(book_id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/audio`, {
        method: "DELETE",
        credentials: "include",
    })

    if (!response.ok) {
        throw new Error("Failed to delete all audio")
    }
}

export async function refresh_chapters(
    book_id: number,
    chapter_numbers: number[],
): Promise<AudiobookChapterQueryResult[]> {
    const response = await fetch(
        `${API_BASE_URL}/api/audiobook/books/${book_id}/chapters/status?chapter_numbers=${chapter_numbers.join(",")}`,
        {
            credentials: "include",
        },
    )

    if (!response.ok) {
        throw new Error("Failed to refresh chapter status")
    }

    const data: AudiobookChapterQueryResult[] = await response.json()
    return data
}
