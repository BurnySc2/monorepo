import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import {
    delete_all_audio,
    delete_all_books,
    delete_book,
    delete_chapter_audio,
    get_available_voices,
    get_book,
    get_books,
    queue_all_chapters,
    queue_chapter_audio,
    refresh_chapters,
    update_book_author,
    update_book_title,
    upload_epub,
} from "./audiobook"

const original_fetch = globalThis.fetch
const mock_fetch = vi.fn()

describe("audiobook API", () => {
    beforeEach(() => {
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
    })

    describe("get_books", () => {
        it("returns array of books on success", async () => {
            const mockBooks = [
                {
                    id: 1,
                    uploaded_by: "user1",
                    book_title: "Test Book",
                    book_author: "Author",
                    custom_book_title: null,
                    custom_book_author: null,
                    chapter_count: 10,
                    upload_date: "2024-01-01",
                },
            ]
            mock_fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockBooks,
            })

            const result = await get_books()
            expect(result).toHaveLength(1)
            expect(result[0].id).toBe(1)
        })

        it("throws on fetch failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(get_books()).rejects.toThrow(/Request failed \/api\/audiobook\/books/)
        })
    })

    describe("get_book", () => {
        it("returns book by id", async () => {
            const mockBook = {
                book: {
                    id: 123,
                    uploaded_by: "user1",
                    book_title: "Test",
                    book_author: "Author",
                    custom_book_title: "",
                    custom_book_author: "",
                    chapter_count: 5,
                    upload_date: "2024-01-01",
                },
                chapters: [],
                available_voices: ["Voice1"],
            }
            mock_fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockBook,
            })

            const result = await get_book(123)
            expect(result?.book.book_title).toBe("Test")
        })

        it("returns null on 404", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                statusText: "Not Found",
            })

            const result = await get_book(999)
            expect(result).toBeNull()
        })

        it("throws on other fetch failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(get_book(123)).rejects.toThrow(/Request failed/)
        })
    })

    describe("delete_book", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(delete_book(123)).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(delete_book(123)).rejects.toThrow(/Request failed/)
        })
    })

    describe("upload_epub", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })
            const file = new File(["content"], "test.epub", { type: "application/epub+zip" })

            await expect(upload_epub(file)).resolves.toBeUndefined()
        })

        it("throws generic error on failure (server detail lost via api_fetch)", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: "Bad Request",
                json: async () => ({ detail: "Invalid file" }),
            })
            const file = new File(["content"], "test.epub", { type: "application/epub+zip" })

            await expect(upload_epub(file)).rejects.toThrow(/Request failed \/api\/audiobook\/upload/)
        })
    })

    describe("get_available_voices", () => {
        it("returns array of voices", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ["Voice1", "Voice2"],
            })

            const result = await get_available_voices()
            expect(result).toEqual(["Voice1", "Voice2"])
        })

        it("throws on fetch failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(get_available_voices()).rejects.toThrow(/Request failed/)
        })
    })

    describe("update_book_title", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(update_book_title(123, "New Title")).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(update_book_title(123, "New Title")).rejects.toThrow(/Request failed/)
        })
    })

    describe("update_book_author", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(update_book_author(123, "New Author")).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(update_book_author(123, "New Author")).rejects.toThrow(/Request failed/)
        })
    })

    describe("queue_chapter_audio", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(
                queue_chapter_audio(123, 1, { value: "af-ZA|edge|af-ZA-AdriNeural|Female" }),
            ).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(queue_chapter_audio(123, 1, { value: "af-ZA|edge|af-ZA-AdriNeural|Female" })).rejects.toThrow(
                /Request failed/,
            )
        })
    })

    describe("delete_chapter_audio", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(delete_chapter_audio(123, 1)).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(delete_chapter_audio(123, 1)).rejects.toThrow(/Request failed/)
        })
    })

    describe("queue_all_chapters", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(
                queue_all_chapters(123, { value: "af-ZA|edge|af-ZA-AdriNeural|Female" }),
            ).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(queue_all_chapters(123, { value: "af-ZA|edge|af-ZA-AdriNeural|Female" })).rejects.toThrow(
                /Request failed/,
            )
        })
    })

    describe("delete_all_audio", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(delete_all_audio(123)).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(delete_all_audio(123)).rejects.toThrow(/Request failed/)
        })
    })

    describe("delete_all_books", () => {
        it("succeeds without error on success", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(delete_all_books()).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(delete_all_books()).rejects.toThrow(/Request failed/)
        })

        it("calls fetch with DELETE and credentials include and correct URL", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: true,
            })

            await delete_all_books()

            expect(mock_fetch).toHaveBeenCalledTimes(1)
            expect(mock_fetch).toHaveBeenCalledWith(
                "http://localhost:8000/api/audiobook/books",
                expect.objectContaining({
                    method: "DELETE",
                    credentials: "include",
                }),
            )
        })
    })

    describe("refresh_chapters", () => {
        it("returns array of chapters on success", async () => {
            const mockChapters = [
                {
                    id: 1,
                    book_id: 123,
                    chapter_number: 1,
                    chapter_title: "Chapter 1",
                    sentence_count: 10,
                    number_in_queue: null,
                    is_converting: false,
                    has_audio: false,
                    minio_object_name: null,
                    minio_presigned_url: "",
                },
            ]
            mock_fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockChapters,
            })

            const result = await refresh_chapters(123, [1])
            expect(result).toHaveLength(1)
            expect(result[0].chapter_number).toBe(1)
        })

        it("throws on fetch failure", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
                statusText: "Server Error",
            })

            await expect(refresh_chapters(123, [1])).rejects.toThrow(/Request failed/)
        })
    })
})
