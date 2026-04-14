import { beforeEach, describe, expect, it, vi } from "vitest"
import { delete_book, get_available_voices, get_book, get_books, upload_epub } from "./audiobook"

const mockFetch = vi.fn()
global.fetch = mockFetch

describe("audiobook API", () => {
    beforeEach(() => {
        vi.clearAllMocks()
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
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockBooks,
            })

            const result = await get_books()
            expect(result).toHaveLength(1)
            expect(result[0].id).toBe(1)
        })

        it("throws on fetch failure", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
            })

            await expect(get_books()).rejects.toThrow("Failed to fetch books")
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
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockBook,
            })

            const result = await get_book(123)
            expect(result?.book.book_title).toBe("Test")
        })

        it("returns null on 404", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
            })

            const result = await get_book(999)
            expect(result).toBeNull()
        })

        it("throws on other fetch failure", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
            })

            await expect(get_book(123)).rejects.toThrow("Failed to fetch book")
        })
    })

    describe("delete_book", () => {
        it("succeeds without error on success", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
            })

            await expect(delete_book(123)).resolves.toBeUndefined()
        })

        it("throws on failure", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
            })

            await expect(delete_book(123)).rejects.toThrow("Failed to delete book")
        })
    })

    describe("upload_epub", () => {
        it("succeeds without error on success", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
            })
            const file = new File(["content"], "test.epub", { type: "application/epub+zip" })

            await expect(upload_epub(file)).resolves.toBeUndefined()
        })

        it("throws on failure with error detail", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: async () => ({ detail: "Invalid file" }),
            })
            const file = new File(["content"], "test.epub", { type: "application/epub+zip" })

            await expect(upload_epub(file)).rejects.toThrow("Invalid file")
        })
    })

    describe("get_available_voices", () => {
        it("returns array of voices", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ["Voice1", "Voice2"],
            })

            const result = await get_available_voices()
            expect(result).toEqual(["Voice1", "Voice2"])
        })

        it("throws on fetch failure", async () => {
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 500,
            })

            await expect(get_available_voices()).rejects.toThrow("Failed to fetch voices")
        })
    })
})
