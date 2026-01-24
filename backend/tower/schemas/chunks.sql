CREATE TABLE IF NOT EXISTS chunks (
  chunk_id STRING,
  document_id STRING,
  page_number INT,
  content STRING,
  embedding ARRAY<FLOAT>,
  created_at TIMESTAMP
);
