-- CreateTable
CREATE TABLE "litestar_audiobook_book" (
    "id" SERIAL NOT NULL,
    "uploaded_by" TEXT NOT NULL,
    "book_title" TEXT NOT NULL,
    "book_author" TEXT NOT NULL,
    "chapter_count" INTEGER NOT NULL,
    "upload_date" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "custom_book_title" TEXT,
    "custom_book_author" TEXT,

    CONSTRAINT "litestar_audiobook_book_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "litestar_audiobook_chapter" (
    "id" SERIAL NOT NULL,
    "book_id" INTEGER NOT NULL,
    "queued" TIMESTAMP(3),
    "started_converting" TIMESTAMP(3),
    "chapter_title" TEXT NOT NULL,
    "chapter_number" INTEGER NOT NULL,
    "word_count" INTEGER NOT NULL,
    "sentence_count" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "minio_object_name" TEXT,
    "audio_settings" JSONB,

    CONSTRAINT "litestar_audiobook_chapter_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "litestar_audiobook_book_id_uploaded_by_idx" ON "litestar_audiobook_book"("id", "uploaded_by");

-- CreateIndex
CREATE INDEX "litestar_audiobook_book_uploaded_by_book_title_book_author_idx" ON "litestar_audiobook_book"("uploaded_by", "book_title", "book_author");

-- CreateIndex
CREATE INDEX "litestar_audiobook_chapter_book_id_chapter_number_idx" ON "litestar_audiobook_chapter"("book_id", "chapter_number");

-- AddForeignKey
ALTER TABLE "litestar_audiobook_chapter" ADD CONSTRAINT "litestar_audiobook_chapter_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "litestar_audiobook_book"("id") ON DELETE CASCADE ON UPDATE CASCADE;
