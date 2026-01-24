# Tower Runbook (PDF -> Chunks -> RAG)

This runbook documents the exact files, paths, and commands used to:
- parse a PDF into chunks,
- store document metadata (hash) in Tower,
- store chunks in Tower (Iceberg),
- run a RAG query over chunks.

## Files and paths

- PDF download: `tests/tower/_tower_local/duolingo_q3fy25.pdf`
- Parsed chunks JSON: `tests/tower/_tower_local/duolingo_chunks.json`
- Parser script: `scripts/parse_pdf.py`
- Tower apps:
  - `backend/tower/apps/document-ingestion`
  - `backend/tower/apps/chunk-storage`
  - `backend/tower/apps/rag-chunk-query`
- ImageKit upload destination:
  - `https://ik.imagekit.io/howtheydidit/hackathon/duolingo_chunks_Fp03ZoRee.json`

## Commands

### 1) Download the PDF

```powershell
$destDir = "tests\tower\_tower_local"
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
Invoke-WebRequest -Uri "https://ik.imagekit.io/howtheydidit/hackathon/Q3FY25%20Duolingo%209-30-25%20Shareholder%20Letter%20Final.pdf?updatedAt=1769284015050" `
  -OutFile "$destDir\duolingo_q3fy25.pdf"
```

### 2) Parse PDF into chunks JSON

```powershell
python scripts\parse_pdf.py --pdf tests\tower\_tower_local\duolingo_q3fy25.pdf --out tests\tower\_tower_local\duolingo_chunks.json
```

### 3) Upload chunks JSON to ImageKit

Uses `IMAGEKIT_PRIVATE_KEY` from `.env`.

```powershell
$env:IMAGEKIT_PRIVATE_KEY = (Select-String -Path .env -Pattern '^IMAGEKIT_PRIVATE_KEY=').Line.Split('=',2)[1]
@'
import os
from pathlib import Path
from imagekitio import ImageKit

imagekit = ImageKit(private_key=os.environ.get("IMAGEKIT_PRIVATE_KEY"))
path = Path("tests/tower/_tower_local/duolingo_chunks.json")
with path.open("rb") as f:
    response = imagekit.files.upload(
        file=f,
        file_name="duolingo_chunks.json",
        folder="/hackathon"
    )
print(response.url)
'@ | python -
```

### 4) Run document ingestion (cloud run)

```powershell
Push-Location "backend\tower\apps\document-ingestion"
tower run --environment=default `
  --parameter=PDF_URL="https://ik.imagekit.io/howtheydidit/hackathon/Q3FY25%20Duolingo%209-30-25%20Shareholder%20Letter%20Final.pdf?updatedAt=1769284015050" `
  --parameter=COMPANY_ID="duolingo" `
  --parameter=VERSION="q3-2025" `
  --parameter=SOURCE_URL="https://ik.imagekit.io/howtheydidit/hackathon/Q3FY25%20Duolingo%209-30-25%20Shareholder%20Letter%20Final.pdf" `
  --parameter=CATALOG="inmutable" `
  --parameter=NAMESPACE="default"
Pop-Location
```

Document ID from this run:

- `2ed0288f-0c6c-49f4-841a-1337188b1b2c`

### 5) Run chunk storage (cloud run)

```powershell
$docId = "2ed0288f-0c6c-49f4-841a-1337188b1b2c"
$chunksUrl = "https://ik.imagekit.io/howtheydidit/hackathon/duolingo_chunks_Fp03ZoRee.json"

Push-Location "backend\tower\apps\chunk-storage"
tower run --environment=default `
  --parameter=DOCUMENT_ID="$docId" `
  --parameter=CHUNKS_PATH="" `
  --parameter=CHUNKS_URL="$chunksUrl" `
  --parameter=CATALOG="inmutable" `
  --parameter=NAMESPACE="default"
Pop-Location
```

### 6) Run RAG query (cloud run)

```powershell
Push-Location "backend\tower\apps\rag-chunk-query"
tower run --environment=default `
  --parameter=DOCUMENT_ID="$docId" `
  --parameter=CHUNKS_PATH="" `
  --parameter=CHUNKS_URL="$chunksUrl" `
  --parameter=QUERY="revenue growth" `
  --parameter=TOP_K="3" `
  --parameter=CATALOG="inmutable" `
  --parameter=NAMESPACE="default"
Pop-Location
```

## Notes

- Remote runs (without `--local`) appear in `https://app.tower.dev/hackthon/default/apps`.
- `chunk-storage` was updated to ignore empty `CHUNKS_PATH` and rely on `CHUNKS_URL` when provided.
