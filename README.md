# ConsultBae AI Automation Assignment

A local-first implementation of the ConsultBae take-home assignment covering:

1. Messy CSV ingestion and identity matching
2. SQLite database storage
3. n8n skill classification automation
4. Audio collection and metadata extraction
5. Data-quality analysis and troubleshooting documentation

The project is designed to run locally without cloud credentials.

## Architecture

```text
                    ┌──────────────────────┐
                    │   3 source CSV files │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   ETL / normalize    │
                    │   identity matching  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      SQLite DB       │
                    │ people / skills /    │
                    │ submissions / review │
                    └──────────┬───────────┘
                               │
                ┌──────────────┴──────────────┐
                │                             │
                ▼                             ▼
       ┌─────────────────┐           ┌─────────────────┐
       │ FastAPI audio   │           │       n8n       │
       │ collection      │           │ classification  │
       └────────┬────────┘           └────────┬────────┘
                │                             │
                ▼                             ▼
       Audio + metadata              Retrieve candidate
       stored in SQLite              skills from FastAPI
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ Classify Skills  │
                                     │ deterministic    │
                                     │ skill rules      │
                                     └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │ FastAPI PATCH   │
                                     │ classification  │
                                     └────────┬────────┘
                                              │
                                              ▼
                                         SQLite DB