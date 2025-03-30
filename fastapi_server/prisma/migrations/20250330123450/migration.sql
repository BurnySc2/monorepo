-- AlterTable
ALTER TABLE "litestar_audiobook_book" ADD COLUMN     "deleted" BOOLEAN NOT NULL DEFAULT false;

-- CreateIndex
CREATE INDEX "litestar_audiobook_chapter_book_id_idx" ON "litestar_audiobook_chapter"("book_id");
