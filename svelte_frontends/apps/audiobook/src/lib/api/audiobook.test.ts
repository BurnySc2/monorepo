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

function mock_500() {
    mock_fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Server Error",
    })
}

function mock_ok(payload?: unknown) {
    if (payload === undefined) {
        mock_fetch.mockResolvedValueOnce({ ok: true })
    } else {
        mock_fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => payload,
        })
    }
}

const audio_settings = { value: "af-ZA|edge|af-ZA-AdriNeural|Female" }

const mock_books_payload = [
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

const mock_chapters_payload = [
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

describe("audiobook API", () => {
    beforeEach(() => {
        vi.clearAllMocks()
        globalThis.fetch = mock_fetch
    })

    afterEach(() => {
        globalThis.fetch = original_fetch
        vi.clearAllMocks()
        vi.unstubAllEnvs()
    })

    describe.each([
        {
            name: "get_books",
            invoke: () => get_books(),
            mock_success: () => mock_ok(mock_books_payload),
            assert_success: (result: Awaited<ReturnType<typeof get_books>>) => {
                expect(result).toHaveLength(1)
                expect(result[0].id).toBe(1)
            },
            failure_pattern: /Request failed \/api\/audiobook\/books/,
        },
        {
            name: "delete_book",
            invoke: () => delete_book(123),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof delete_book>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "get_available_voices",
            invoke: () => get_available_voices(),
            mock_success: () => mock_ok(["Voice1", "Voice2"]),
            assert_success: (result: Awaited<ReturnType<typeof get_available_voices>>) => {
                expect(result).toEqual(["Voice1", "Voice2"])
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "update_book_title",
            invoke: () => update_book_title(123, "New Title"),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof update_book_title>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "update_book_author",
            invoke: () => update_book_author(123, "New Author"),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof update_book_author>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "queue_chapter_audio",
            invoke: () => queue_chapter_audio(123, 1, audio_settings),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof queue_chapter_audio>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "delete_chapter_audio",
            invoke: () => delete_chapter_audio(123, 1),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof delete_chapter_audio>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "queue_all_chapters",
            invoke: () => queue_all_chapters(123, audio_settings),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof queue_all_chapters>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "delete_all_audio",
            invoke: () => delete_all_audio(123),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof delete_all_audio>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "delete_all_books",
            invoke: () => delete_all_books(),
            mock_success: () => mock_ok(),
            assert_success: async (result: Awaited<ReturnType<typeof delete_all_books>>) => {
                expect(result).toBeUndefined()
            },
            failure_pattern: /Request failed/,
        },
        {
            name: "refresh_chapters",
            invoke: () => refresh_chapters(123, [1]),
            mock_success: () => mock_ok(mock_chapters_payload),
            assert_success: (result: Awaited<ReturnType<typeof refresh_chapters>>) => {
                expect(result).toHaveLength(1)
                expect(result[0].chapter_number).toBe(1)
            },
            failure_pattern: /Request failed/,
        },
    ])("$name", ({ invoke, mock_success, assert_success, failure_pattern }) => {
        it("succeeds without error on success", async () => {
            mock_success()
            const result = await (invoke() as Promise<never>)
            await assert_success(result as never)
        })

        it("throws on fetch failure", async () => {
            mock_500()
            await expect(invoke()).rejects.toThrow(failure_pattern)
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
            mock_500()

            await expect(get_book(123)).rejects.toThrow(/Request failed/)
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

        it("throws friendly already-uploaded error on 409", async () => {
            mock_fetch.mockResolvedValueOnce({
                ok: false,
                status: 409,
                statusText: "Conflict",
                json: async () => ({ detail: "Already uploaded" }),
            })
            const file = new File(["content"], "test.epub", { type: "application/epub+zip" })

            await expect(upload_epub(file)).rejects.toThrow(/already uploaded/i)
        })
    })

    describe("delete_all_books url", () => {
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
})
