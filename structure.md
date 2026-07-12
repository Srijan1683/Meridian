# Project Structure

```text
Meridian/
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── dependencies.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── prompts.py
│   │   ├── research_agent.py
│   │   └── tools.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── memory.py
│   │   ├── research.py
│   │   ├── sessions.py
│   │   ├── sources.py
│   │   └── websocket.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── chromadb.py
│   │   ├── postgres.py
│   │   ├── migrations/
│   │   │   └── 001_initial_schema.sql
│   │   └── repositories/
│   │       ├── memory_jobs.py
│   │       ├── messages.py
│   │       ├── sessions.py
│   │       └── sources.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── long_term.py
│   │   ├── manager.py
│   │   ├── short_term.py
│   │   └── summarizer.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── memory.py
│   │   ├── research.py
│   │   ├── sessions.py
│   │   ├── sources.py
│   │   └── websocket.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── perplexity.py
│   │   ├── source_tracker.py
│   │   └── tavily.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── citation_service.py
│   │   ├── research_service.py
│   │   ├── session_service.py
│   │   └── token_budget.py
│   └── workers/
│       ├── __init__.py
│       ├── jobs.py
│       └── memory_worker.py
├── scripts/
│   ├── init_db.py
│   ├── run_worker.py
│   ├── seed_memory.py
│   ├── test_embeddings.py
│   ├── test_long_term_memory.py
│   ├── test_short_term_memory.py
│   └── test_summarizer.py
└── tests/
    ├── test_citation.py
    ├── test_memory.py
    ├── test_research.py
    ├── test_short_term_memory.py
    ├── test_sources.py
    └── test_websocket.py
```

Ignored local/generated paths are intentionally omitted, including `.env`, `.git/`, `.venv/`, `__pycache__/`, and `chroma_data/`.
