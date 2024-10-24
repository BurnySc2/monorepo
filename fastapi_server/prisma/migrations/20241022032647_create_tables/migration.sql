-- CreateEnum
CREATE TYPE "Status" AS ENUM ('NoFile', 'HasFile', 'Queued', 'Downloading', 'Downloaded');

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

-- CreateTable
CREATE TABLE "litestar_telegram_channel" (
    "id" SERIAL NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "channel_title" TEXT NOT NULL,
    "channel_username" TEXT,
    "creation_date" TIMESTAMP(3) NOT NULL,
    "participants" BIGINT NOT NULL,
    "last_parsed" TIMESTAMP(3) NOT NULL DEFAULT '2000-01-01 00:00:00'::timestamp without time zone,

    CONSTRAINT "litestar_telegram_channel_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "litestar_telegram_message" (
    "id" SERIAL NOT NULL,
    "channel_id" BIGINT NOT NULL,
    "message_id" BIGINT NOT NULL,
    "message_date" TIMESTAMP(3) NOT NULL,
    "message_text" TEXT,
    "amount_of_reactions" BIGINT NOT NULL DEFAULT 0,
    "amount_of_comments" BIGINT NOT NULL DEFAULT 0,
    "status" "Status" NOT NULL DEFAULT 'NoFile',
    "file_downloadinfo_id" BIGINT,
    "file_downloadinfo_access_hash" BIGINT,
    "file_downloadinfo_file_reference" BYTEA,
    "downloading_start_time" TIMESTAMP(3),
    "mime_type" TEXT,
    "file_extension" TEXT,
    "file_size_bytes" BIGINT,
    "file_duration_seconds" DOUBLE PRECISION,
    "file_height" INTEGER,
    "file_width" INTEGER,
    "minio_object_name" TEXT,
    "downloading_retry_attempt" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "litestar_telegram_message_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "litestar_audiobook_book_id_uploaded_by_idx" ON "litestar_audiobook_book"("id", "uploaded_by");

-- CreateIndex
CREATE INDEX "litestar_audiobook_book_uploaded_by_book_title_book_author_idx" ON "litestar_audiobook_book"("uploaded_by", "book_title", "book_author");

-- CreateIndex
CREATE INDEX "litestar_audiobook_chapter_book_id_chapter_number_idx" ON "litestar_audiobook_chapter"("book_id", "chapter_number");

-- CreateIndex
CREATE UNIQUE INDEX "litestar_telegram_channel_channel_id_key" ON "litestar_telegram_channel"("channel_id");

-- CreateIndex
CREATE INDEX "litestar_telegram_channel_channel_id_idx" ON "litestar_telegram_channel"("channel_id");

-- CreateIndex
CREATE INDEX "litestar_telegram_channel_channel_title_idx" ON "litestar_telegram_channel"("channel_title");

-- CreateIndex
CREATE INDEX "litestar_telegram_channel_channel_username_idx" ON "litestar_telegram_channel"("channel_username");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_channel_id_message_id_idx" ON "litestar_telegram_message"("channel_id", "message_id");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_amount_of_comments_idx" ON "litestar_telegram_message"("amount_of_comments" DESC);

-- CreateIndex
CREATE INDEX "litestar_telegram_message_amount_of_reactions_idx" ON "litestar_telegram_message"("amount_of_reactions" DESC);

-- CreateIndex
CREATE INDEX "litestar_telegram_message_channel_id_idx" ON "litestar_telegram_message"("channel_id");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_file_duration_seconds_idx" ON "litestar_telegram_message"("file_duration_seconds");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_file_extension_idx" ON "litestar_telegram_message"("file_extension");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_file_height_idx" ON "litestar_telegram_message"("file_height");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_file_size_bytes_idx" ON "litestar_telegram_message"("file_size_bytes");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_file_width_idx" ON "litestar_telegram_message"("file_width");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_message_date_idx" ON "litestar_telegram_message"("message_date" DESC);

-- CreateIndex
CREATE INDEX "litestar_telegram_message_message_id_idx" ON "litestar_telegram_message"("message_id");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_message_text_idx" ON "litestar_telegram_message" USING GIN ("message_text" gin_trgm_ops);

-- CreateIndex
CREATE INDEX "litestar_telegram_message_mime_type_idx" ON "litestar_telegram_message"("mime_type");

-- CreateIndex
CREATE INDEX "litestar_telegram_message_status_idx" ON "litestar_telegram_message"("status");

-- AddForeignKey
ALTER TABLE "litestar_audiobook_chapter" ADD CONSTRAINT "litestar_audiobook_chapter_book_id_fkey" FOREIGN KEY ("book_id") REFERENCES "litestar_audiobook_book"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "litestar_telegram_message" ADD CONSTRAINT "litestar_telegram_message_channel_id_fkey" FOREIGN KEY ("channel_id") REFERENCES "litestar_telegram_channel"("channel_id") ON DELETE CASCADE ON UPDATE CASCADE;
