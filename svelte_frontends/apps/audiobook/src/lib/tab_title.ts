export function get_tab_title(
    live_title: string,
    live_author: string,
    saved_custom_title: string | null | undefined,
    saved_custom_author: string | null | undefined,
    base_title: string,
    base_author: string,
    has_book: boolean,
): string {
    if (!has_book) {
        return "Audiobook Converter"
    }
    const title = live_title.trim() || saved_custom_title?.trim() || base_title.trim() || ""
    const author = live_author.trim() || saved_custom_author?.trim() || base_author.trim() || ""
    if (author && title) {
        return `${author} - ${title}`
    }
    if (title) {
        return title
    }
    if (author) {
        return author
    }
    return "Audiobook Converter"
}
