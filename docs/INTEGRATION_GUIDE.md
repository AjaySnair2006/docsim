# Integration Guide — Connecting the 3 Modules

The backend is built so each teammate's module plugs in at exactly **one
file**, without touching routes, validation, or the frontend at all. Until a
module is plugged in, a lightweight stub keeps that step working so the team
can demo the full pipeline early.

```
Upload (frontend)
   │
   ▼
POST /compare  (backend/app/routes/compare.py)
   │
   ├─► pdf_module_adapter.extract_document()        → Teammate 1
   │
   ├─► similarity_module_adapter.compute()          → Teammate 2
   │
   ├─► report_module_adapter.analyze()               ┐
   └─► report_module_adapter.generate_report()       ┘ Teammate 3
   │
   ▼
JSON response + downloadable PDF report
```

## Teammate 1 — PDF Processing & Text Extraction

**File to edit:** `backend/app/services/pdf_module_adapter.py`

1. Put your package under `backend/app/external/pdf_processing/`.
2. Expose a function:
   ```python
   def extract_text_from_pdf(file_path: str) -> dict:
       return {
           "filename": "docA.pdf",
           "total_pages": 5,
           "pages": [{"page_number": 1, "text": "..."}, ...],
       }
   ```
3. In `pdf_module_adapter.py`, update `_call_real_pdf_module()`:
   ```python
   from app.external.pdf_processing.extractor import extract_text_from_pdf
   ```
4. Test it: `POST /compare` with two sample PDFs and confirm real text shows
   up in the JSON response instead of the stub's `pypdf`-based output.

## Teammate 2 — AI Semantic Similarity

**File to edit:** `backend/app/services/similarity_module_adapter.py`

1. Put your package under `backend/app/external/similarity/`.
2. Expose a function:
   ```python
   def compute_similarity(doc_a: dict, doc_b: dict, api_key: str = "") -> dict:
       return {
           "overall_similarity": 82.5,
           "page_pair_scores": [
               {"doc_a_page": 1, "doc_b_page": 1, "similarity_score": 91.2},
               ...
           ],
       }
   ```
   `doc_a` / `doc_b` are the dicts produced by Teammate 1's module (same
   shape as `extract_text_from_pdf`'s return value).
3. If your model needs an API key, add it to `backend/.env` as
   `AI_MODULE_API_KEY=...` — never hardcode it. It's already read via
   `app.config.settings.AI_MODULE_API_KEY` and passed into your function.
4. Update `_call_real_similarity_module()`'s import.

## Teammate 3 — Comparison Analysis & PDF Report Generation

**File to edit:** `backend/app/services/report_module_adapter.py`

1. Put your package under `backend/app/external/report/`.
2. Expose two functions:
   ```python
   def analyze_comparison(doc_a: dict, doc_b: dict, similarity_result: dict) -> dict:
       return {
           "similar_sections": [ ... ],   # see models.py: SimilarSection shape
           "page_wise_stats": [ ... ],    # see models.py: PageStat shape
       }

   def generate_pdf_report(comparison_data: dict, output_path: str) -> str:
       # comparison_data has: comparison_id, document_a_name, document_b_name,
       # overall_similarity, similar_sections, page_wise_stats,
       # total_pages_a, total_pages_b
       ...
       return output_path
   ```
3. Update `_call_real_analysis_module()` and `_call_real_report_module()`'s
   imports.

## Shared data contract

The exact field names/types every module should produce or consume are
defined once, in `backend/app/models.py` (`ExtractedDocument`,
`SimilarSection`, `PageStat`, `ComparisonResult`). Treat that file as the
source of truth if there's ever a disagreement about a field name.

## Checklist before merging a real module in

- [ ] Function signature matches what the adapter imports
- [ ] Returns plain `dict`s / JSON-serializable values (not custom classes)
- [ ] Raises a normal Python exception on failure (the adapters already wrap
      it into the right HTTP error — you don't need to handle HTTP yourself)
- [ ] No API keys or secrets hardcoded — read from `app.config.settings`
- [ ] Tested standalone AND through `POST /compare` end-to-end
