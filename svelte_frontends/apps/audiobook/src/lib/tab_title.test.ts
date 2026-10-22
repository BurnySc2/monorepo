import { describe, expect, it } from "vitest"
import { get_tab_title } from "./tab_title"

describe("get_tab_title", () => {
    it("combines author and title", () => {
        expect(get_tab_title("Title", "Author", null, null, "Base Title", "Base Author", true)).toBe("Author - Title")
    })

    it("returns title only when author is missing", () => {
        expect(get_tab_title("My Title", "", null, null, "", "", true)).toBe("My Title")
    })

    it("returns fallback when there is no book", () => {
        expect(get_tab_title("Title", "Author", null, null, "Base Title", "Base Author", false)).toBe(
            "Audiobook Converter",
        )
    })
})
