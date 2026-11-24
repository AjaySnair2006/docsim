# AI-Based Document Similarity Detection System

3rd-year B.E. AI/ML mini project. Four-person team, four responsibilities:

| # | Area | Owner |
|---|------|-------|
| 1 | PDF processing & text extraction | AJAY 1ST |
| 2 | AI semantic similarity | AJAY 2ND |
| 3 | Comparison analysis & PDF report generation | AJAY 3RD |
| 4 | **Application layer: backend API + frontend UI** | **AJAY**|

This repo contains ONLY the application layer (#4): a FastAPI backend that
orchestrates the other three modules, and a React frontend that lets a user
upload two PDFs, see the comparison, and download a report.

## Folder structure

```
docsim-project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── config.py                # env-based configuration
│   │   ├── models.py                # Pydantic schemas (the data "contract")
│   │   ├── routes/
│   │   │   ├── health.py            # GET /health
│   │   │   ├── compare.py           # POST /compare (main pipeline)
│   │   │   └── report.py            # GET /download-report/{id}
│   │   ├── services/
│   │   │   ├── pdf_module_adapter.py         # calls AJAY S 1st module
│   │   │   ├── similarity_module_adapter.py  # calls AJAY S 2st module
│   │   │   ├── report_module_adapter.py      # calls AJAY S 3st module
│   │   │   └── report_store.py               # in-memory report registry
│   │   ├── utils/
│   │   │   ├── validators.py        # PDF upload validation
│   │   │   └── file_handler.py      # save/cleanup temp files
│   │   └── external/                # <- teammates drop their real code here
│   │       ├── pdf_processing/
│   │       ├── similarity/
│   │       └── report/
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/
│   ├── src/
│   │   ├── App.jsx / App.css
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── ResultsDisplay.jsx
│   │   │   └── ErrorMessage.jsx
│   │   └── api/api.js               # axios client for the backend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── docs/
    ├── API_DOCUMENTATION.md
    └── INTEGRATION_GUIDE.md
```

## Quick start

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000`. Interactive docs at `/docs`.

Until the real teammate modules are plugged in, the backend automatically
falls back to lightweight implementations for PDF text extraction, word-shingle
text overlap, and PDF report generation. It also computes a separate semantic
content score with a sentence-transformer model, downloaded on first comparison.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend runs at `http://localhost:5173` and talks to the backend at the URL
set in `frontend/.env` (`VITE_API_BASE_URL`).

### 3. Try it

Open `http://localhost:5173`, upload two PDFs, click **Compare Documents**.

## Connecting the other three modules

See [`docs/INTEGRATION_GUIDE.md`](docs/INTEGRATION_GUIDE.md) — each teammate
only needs to drop their code into one `backend/app/external/<module>/`
folder and match one function signature; no other file needs to change.

## API reference

See [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md) for endpoints,
request/response examples, and error codes.
