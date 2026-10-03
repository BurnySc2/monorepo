import { create_persisted_state } from "@repo/persisted-state"
import { z } from "zod"

export const PdfSettingsSchema = z.object({
    chapter_mode: z.enum(["auto", "outline", "heuristic", "single"]).default("auto"),
    heuristic_sensitivity: z.enum(["low", "medium", "high"]).default("medium"),
    page_start: z.number().nullable().default(null),
    page_end: z.number().nullable().default(null),
    min_chapter_chars: z.number().default(500),
    max_chapters: z.number().default(300),
    include_images: z.boolean().default(true),
    strip_headers: z.boolean().default(true),
    clean_hyphens: z.boolean().default(true),
    use_cover: z.boolean().default(true),
    language: z.string().nullable().default(null),
})

export type PdfSettings = z.infer<typeof PdfSettingsSchema>

const STORAGE_KEY = "pdf_to_epub_settings"

const persisted = create_persisted_state(STORAGE_KEY, PdfSettingsSchema, PdfSettingsSchema.parse({}))

export const pdf_settings = persisted.state

export const is_loading = persisted.is_loading

export function load_pdf_settings(): PdfSettings {
    return { ...persisted.state }
}

export function save_pdf_settings(settings: PdfSettings): void {
    Object.assign(persisted.state, PdfSettingsSchema.parse(settings))
}

export function reset_pdf_settings(): void {
    persisted.reset()
}
