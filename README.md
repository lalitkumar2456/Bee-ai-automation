# ConsultBae AI Automation Assignment — Local Edition

A local-first implementation of CSV ingestion, cautious identity matching, audio collection, and n8n automation. It uses SQLite and filesystem storage so it runs without Docker, cloud accounts, or credentials.

## Included

- CSV profiling and ingestion with normalization, provenance, source-specific repairs, and a review queue.
- SQLite relational schema for people, source records, skills, audio submissions, and manual review.
- FastAPI audio app: name/phone identification, upload, metadata analysis, playback, and submission list.
- Importable local n8n skill-classification workflow.
- Data-quality report and stuck-log template.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Add the raw source files to `data/` (they remain unchanged and are git-ignored):

```text
source1_naukri_applicants.csv
source2_gig_workers.csv
source3_cbnexus_contacts.csv
```

```powershell
python -m etl.profile
python -m etl.ingest
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. WAV audio metadata works with Python alone; for MP3/M4A metadata, install FFmpeg locally and put `ffprobe` on PATH.

## n8n

Import [n8n/skill-tagging-workflow.json](n8n/skill-tagging-workflow.json) into a local n8n installation. It creates `POST /webhook/consultbae-classify` and categorizes a body containing `person_id` and comma-separated `skills`. It has no cloud/LLM dependency. Add a database-update node after the code node to persist its deterministic result.

## Matching policy

See [docs/data_issues.md](docs/data_issues.md). Match by exact normalized email, then phone, then uniquely resolvable name plus city. Ambiguous records are never automatically merged.
