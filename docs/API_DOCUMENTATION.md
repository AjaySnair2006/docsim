# API Documentation

Base URL (local dev): `http://localhost:8000`
Interactive Swagger UI: `http://localhost:8000/docs`

---

## GET /health

Liveness check.

**Response 200**
```json
{
  "status": "ok",
  "app_name": "AI Document Similarity Detection System",
  "version": "1.0.0"
}
```

---

## POST /compare

Uploads two PDFs and runs the full pipeline (extraction → similarity →
analysis → report generation).

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `document_a` | file (.pdf) | yes | First document |
| `document_b` | file (.pdf) | yes | Second document |

**Validation rules:** must be a `.pdf` file, non-empty, valid PDF signature,
and no larger than 10 MB by default, matching the frontend upload limit.
The limit can be changed with `MAX_FILE_SIZE_MB` in the backend environment.

`overall_similarity` measures wording overlap. If the optional teammate
similarity module is not installed, its fallback uses normalized three-word
phrase overlap and accounts for unmatched content in both documents. It
tolerates sentence reordering, but does not reliably detect paraphrases.

`content_similarity` is a separate sentence-transformer embedding score that
compares page meaning and can surface paraphrased content. The default model is
`sentence-transformers/all-MiniLM-L6-v2`; it is downloaded the first time a
comparison runs. Configure `CONTENT_SIMILARITY_MODEL` and
`CONTENT_SIMILARITY_THRESHOLD` to change the model or page-match threshold.
Embedding scores are similarity estimates, not probabilities or plagiarism
findings.

### Example request (curl)
```bash
curl -X POST http://localhost:8000/compare \
  -F "document_a=@/path/to/docA.pdf" \
  -F "document_b=@/path/to/docB.pdf"
```

### Example request (JavaScript / axios)
```js
const formData = new FormData();
formData.append("document_a", fileA);
formData.append("document_b", fileB);
await axios.post("http://localhost:8000/compare", formData);
```

### Response 200
```json
{
  "comparison_id": "9f3a1c2b7e4d4a1b8f6a2c3d4e5f6a7b",
  "document_a_name": "docA.pdf",
  "document_b_name": "docB.pdf",
  "overall_similarity": 82.4,
  "content_similarity": 78.6,
  "similar_sections": [
    {
      "doc_a_page": 1,
      "doc_b_page": 1,
      "doc_a_excerpt": "Introduction to machine learning...",
      "doc_b_excerpt": "An introduction to machine learning...",
      "similarity_score": 91.2
    }
  ],
  "page_wise_stats": [
    {
      "page_number": 1,
      "matched_page_in_other_doc": 1,
      "similarity_score": 91.2
    }
  ],
  "content_similar_sections": [
    {
      "doc_a_page": 1,
      "doc_b_page": 2,
      "doc_a_excerpt": "A passage explaining the central finding...",
      "doc_b_excerpt": "A paraphrased account of the main result...",
      "similarity_score": 86.1
    }
  ],
  "content_page_wise_stats": [
    {
      "page_number": 1,
      "matched_page_in_other_doc": 2,
      "similarity_score": 86.1
    }
  ],
  "total_pages_a": 5,
  "total_pages_b": 6,
  "report_download_url": "/download-report/9f3a1c2b7e4d4a1b8f6a2c3d4e5f6a7b"
}
```

### Error responses

All errors follow this shape (FastAPI wraps it under `detail`):

```json
{
  "detail": {
    "error_code": "UNSUPPORTED_FILE_TYPE",
    "message": "Unsupported file type '.docx'. Only PDF files are allowed."
  }
}
```

| HTTP Status | error_code | Meaning |
|---|---|---|
| 400 | `MISSING_FILENAME` | No filename on the upload |
| 400 | `UNSUPPORTED_FILE_TYPE` | File is not a `.pdf` |
| 400 | `EMPTY_FILE` | File has zero bytes |
| 400 | `FILE_TOO_LARGE` | File exceeds `MAX_FILE_SIZE_MB` |
| 400 | `CORRUPT_OR_INVALID_PDF` | File doesn't start with `%PDF-` |
| 422 | `PDF_PROCESSING_FAILED` | Text extraction module raised an error |
| 500 | `SIMILARITY_COMPUTATION_FAILED` | Similarity module raised an error |
| 500 | `REPORT_GENERATION_FAILED` | Analysis/report module raised an error |
| 500 | `INTERNAL_ERROR` / `INTERNAL_SERVER_ERROR` | Unhandled server error |

---

## GET /download-report/{comparison_id}

Downloads the PDF report for a previously run comparison.
`comparison_id` comes from the `report_download_url` field of a `/compare`
response.

**Response 200:** binary `application/pdf` stream.

**Response 404**
```json
{
  "detail": {
    "error_code": "REPORT_NOT_FOUND",
    "message": "No report found for comparison_id '...'. It may have expired or the ID is incorrect."
  }
}
```

> Note: the report registry is in-memory (see
> `backend/app/services/report_store.py`). Reports are only available while
> the backend process is running and haven't been looked up after a restart.
> Swap in a database/file-based store if you need persistence across restarts.
