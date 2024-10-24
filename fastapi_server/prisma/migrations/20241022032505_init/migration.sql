-- Create extension for index:
-- @@index([message_text(ops: raw("gin_trgm_ops"))], type: Gin)
CREATE EXTENSION IF NOT EXISTS pg_trgm;
