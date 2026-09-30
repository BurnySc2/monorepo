// API service for Audiobook feature

import { api_fetch, get_api_error_status } from "@repo/api-client"
import type {
    BookListItemSchema as AudiobookBook,
    ChapterDetail as AudiobookChapterQueryResult,
    QueueChapterRequest as AudioSettings,
    BookWithChapters,
    VoiceInfo,
} from "@repo/api-types"
import { mock_book_data } from "./mock_data"

const USE_MOCK = typeof import.meta.env !== "undefined" && import.meta.env.VITE_USE_MOCK === "true"

export async function get_books(): Promise<AudiobookBook[]> {
    const response = await api_fetch("/api/audiobook/books")
    return response.json()
}

export async function get_book(book_id: number): Promise<BookWithChapters | null> {
    if (USE_MOCK) {
        console.log("[MOCK] get_book called, returning mock data")
        return mock_book_data
    }

    try {
        const response = await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}`)
        return response.json()
    } catch (error) {
        if (get_api_error_status(error) === 404) {
            return null
        }
        if (error instanceof Error && /\/api\/audiobook\/books\/[^\s]*: 404(?:[ ,]|$)/.test(error.message)) {
            return null
        }
        throw error
    }
}

export async function upload_epub(file: File): Promise<void> {
    const formData = new FormData()
    formData.append("file", file)

    try {
        await api_fetch("/api/audiobook/upload", {
            method: "POST",
            body: formData,
        })
    } catch (error) {
        if (get_api_error_status(error) === 409) {
            const friendly = new Error("Book already uploaded: this EPUB has already been uploaded")
            ;(friendly as Error & { status?: number }).status = 409
            throw friendly
        }
        throw error
    }
}

export async function get_available_voices(): Promise<VoiceInfo[]> {
    const response = await api_fetch("/tts-generate/voices-audiobook")
    return response.json()
}

export async function update_book_title(book_id: number, title: string): Promise<void> {
    await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}/title`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ title }),
    })
}

export async function update_book_author(book_id: number, author: string): Promise<void> {
    await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}/author`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ author }),
    })
}

export async function queue_chapter_audio(
    book_id: number,
    chapter_id: number,
    audio_settings: AudioSettings,
): Promise<void> {
    await api_fetch(
        `/api/audiobook/books/${encodeURIComponent(String(book_id))}/chapters/${encodeURIComponent(String(chapter_id))}/queue`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(audio_settings),
        },
    )
}

export async function delete_chapter_audio(book_id: number, chapter_id: number): Promise<void> {
    await api_fetch(
        `/api/audiobook/books/${encodeURIComponent(String(book_id))}/chapters/${encodeURIComponent(String(chapter_id))}`,
        {
            method: "DELETE",
        },
    )
}

export async function queue_all_chapters(book_id: number, audio_settings: AudioSettings): Promise<void> {
    await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}/queue-all`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(audio_settings),
    })
}

export async function delete_book(book_id: number): Promise<void> {
    await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}`, {
        method: "DELETE",
    })
}

export async function delete_all_books(): Promise<void> {
    await api_fetch("/api/audiobook/books", {
        method: "DELETE",
    })
}

export async function delete_all_audio(book_id: number): Promise<void> {
    await api_fetch(`/api/audiobook/books/${encodeURIComponent(String(book_id))}/audio`, {
        method: "DELETE",
    })
}

export async function refresh_chapters(
    book_id: number,
    chapter_numbers: number[],
): Promise<AudiobookChapterQueryResult[]> {
    const response = await api_fetch(
        `/api/audiobook/books/${encodeURIComponent(String(book_id))}/chapters/status?chapter_numbers=${encodeURIComponent(chapter_numbers.join(","))}`,
    )

    const data: AudiobookChapterQueryResult[] = await response.json()
    return data
}
