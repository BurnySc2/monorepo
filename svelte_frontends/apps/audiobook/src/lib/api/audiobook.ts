// Placeholder API service - will be replaced with actual API calls when backend is running
import type { AudiobookBook, AudiobookChapterQueryResult, BookWithChapters } from "$lib/types/audiobook"

const API_BASE_URL = "http://localhost:8000"

// Placeholder data
const PLACEHOLDER_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

function create_placeholder_books(): AudiobookBook[] {
    return []
}

export async function get_books(): Promise<AudiobookBook[]> {
    // TODO: Replace with actual API call when backend is running
    // const response = await fetch(`${API_BASE_URL}/api/audiobook/books`);
    // if (!response.ok) throw new Error("Failed to fetch books");
    // return response.json();

    console.log("[API] get_books called (placeholder)")
    return create_placeholder_books()
}

export async function get_book(book_id: number): Promise<BookWithChapters | null> {
    // TODO: Replace with actual API call when backend is running
    // const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}`);
    // if (!response.ok) return null;
    // return response.json();

    console.log("[API] get_book called with book_id:", book_id, "(placeholder)")
    return null
}

export async function upload_epub(file: File): Promise<number> {
    // TODO: Replace with actual API call when backend is running
    // const formData = new FormData();
    // formData.append("file", file);
    // const response = await fetch(`${API_BASE_URL}/api/audiobook/upload`, {
    //     method: "POST",
    //     body: formData,
    // });
    // if (!response.ok) throw new Error("Failed to upload book");
    // return response.json();

    console.log("[API] upload_epub called with file:", file.name, "(placeholder)")
    throw new Error("Upload not implemented yet")
}

export async function get_available_voices(): Promise<string[]> {
    // TODO: Replace with actual API call when backend is running
    // const response = await fetch(`${API_BASE_URL}/api/audiobook/voices`);
    // if (!response.ok) throw new Error("Failed to fetch voices");
    // return response.json();

    console.log("[API] get_available_voices called (placeholder)")
    return PLACEHOLDER_VOICES
}

export async function update_book_title(book_id: number, title: string): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    // await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/title`, {
    //     method: "PUT",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ title }),
    // });

    console.log("[API] update_book_title called with book_id:", book_id, "title:", title, "(placeholder)")
}

export async function update_book_author(book_id: number, author: string): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    console.log("[API] update_book_author called with book_id:", book_id, "author:", author, "(placeholder)")
}

export async function queue_chapter_audio(chapter_id: number): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    // await fetch(`${API_BASE_URL}/api/audiobook/chapters/${chapter_id}/queue`, {
    //     method: "POST",
    // });

    console.log("[API] queue_chapter_audio called with chapter_id:", chapter_id, "(placeholder)")
}

export async function delete_chapter_audio(chapter_id: number): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    console.log("[API] delete_chapter_audio called with chapter_id:", chapter_id, "(placeholder)")
}

export async function queue_all_chapters(book_id: number): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    console.log("[API] queue_all_chapters called with book_id:", book_id, "(placeholder)")
}

export async function download_book(book_id: number): Promise<string> {
    // TODO: Replace with actual API call when backend is running
    // const response = await fetch(`${API_BASE_URL}/api/audiobook/books/${book_id}/download`);
    // if (!response.ok) throw new Error("Failed to get download URL");
    // const data = await response.json();
    // return data.download_url;

    console.log("[API] download_book called with book_id:", book_id, "(placeholder)")
    throw new Error("Download not implemented yet")
}

export async function delete_book(book_id: number): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    console.log("[API] delete_book called with book_id:", book_id, "(placeholder)")
}

export async function delete_all_audio(book_id: number): Promise<void> {
    // TODO: Replace with actual API call when backend is running
    console.log("[API] delete_all_audio called with book_id:", book_id, "(placeholder)")
}
