CREATE TABLE IF NOT EXISTS documents (
  document_id STRING,
  company_id STRING,
  version STRING,
  sha256 STRING,
  source_url STRING,
  created_at TIMESTAMP
);
