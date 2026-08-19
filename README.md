# Meridian

Meridian is a full-stack AI research workspace that combines web search, cited synthesis, short-term session memory, long-term memory summarization, and a responsive React interface.

It supports two research modes:

- **Normal mode:** faster answers using up to 2 targeted searches.
- **Deep mode:** slower, more thorough research using up to 6 searches with WebSocket progress streaming.

The project is designed to demonstrate practical AI application architecture: retrieval-augmented memory, source tracking, citation validation, async background jobs, streaming UX, and persistent session storage.

## Features

- **Memory-aware research**
  Retrieves short-term session memory and long-term cross-session summaries before generating answers.

- **Two research modes**
  Normal mode prioritizes speed. Deep mode searches from multiple angles and handles gaps, limitations, and contradictions.

- **Citations and source tracking**
  Every returned source is persisted in Postgres, inline citations are validated, and source lists are appended to responses.

- **WebSocket streaming**
  Deep research streams memory, search, source, content, done, and error events to the frontend.

- **Short-term and long-term memory**
  Session interactions are stored in ChromaDB. Ended sessions can be summarized into long-term memories through a worker.

- **Responsive frontend**
  React + Vite + Tailwind UI with dark themes, mode-based color switching, query history, markdown/code rendering, mobile layout, and scrollable response panels.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- pydantic-settings
- asyncpg
- PostgreSQL
- ChromaDB
- OpenAI Python SDK
- OpenAI-compatible model routing through `openai_base_url`
- Tavily web search
- tiktoken
- httpx
- pytest
- pytest-asyncio


## Architecture

```text
frontend/
  React + Vite client
  - normal research over HTTP
  - deep research over WebSocket
  - query history in localStorage
  - markdown and code block rendering

app/
  FastAPI backend
  - /research HTTP endpoint
  - /ws/research WebSocket endpoint
  - /sessions endpoints
  - /memory endpoints
  - /sources endpoints

PostgreSQL
  - sessions
  - conversation history
  - sources
  - source citations
  - memory jobs
  - API/tool tracking tables

ChromaDB
  - short-term session memory collections
  - long-term memory collection

Worker
  - claims memory jobs
  - summarizes ended sessions
  - stores long-term memory
```

## Research Flow

### Normal Mode

1. Create or reuse a session.
2. Retrieve short-term session memory.
3. Retrieve long-term memory.
4. Run up to 2 web searches.
5. Store sources in Postgres.
6. Synthesize a cited response.
7. Validate citation markers.
8. Store citation mappings.
9. Store the interaction in short-term memory.

### Deep Mode

1. Connect through WebSocket.
2. Create or reuse a session.
3. Emit memory event.
4. Run up to 6 iterative searches.
5. Emit search and source events.
6. Synthesize a comprehensive cited response.
7. Stream content chunks to the client.
8. Store sources, citations, response, and short-term memory.

## Quantified Implementation

- **19 automated tests** currently pass.
- **40 Python files** in the backend app package.
- **8 Python test files**.
- **3 frontend source files**.
- **4,307 lines** across app Python files, tests, frontend source, and core config files measured at documentation time.
- **2 searches** maximum in normal mode.
- **6 searches** maximum in deep mode.
- **400 characters** maximum Tavily query length before trimming.
- **600 characters** per streamed response chunk.
- **5 short-term memories** retrieved per research request.
- **3 long-term memories** retrieved per research request.
- **0.7 similarity threshold** for normal vector memory retrieval.
- **8 query history items** retained in the frontend.
- **8,191 tokens** maximum embedding chunk size.
- **100 tokens** overlap between embedding chunks.
- **9 relational tables** in the initial Postgres schema.

More detailed technical notes are in [`documentation`](documentation).

## API Surface

| Area | Endpoint | Purpose |
| --- | --- | --- |
| Health | `GET /health` | Check backend availability |
| Research | `POST /research` | Run non-streaming normal/deep research |
| Research | `GET /research/{session_id}/latest` | Fetch latest completed assistant result |
| WebSocket | `WS /ws/research` | Stream deep research progress and content |
| Sessions | `POST /sessions/{session_id}/end` | End a session and optionally queue memory summarization |
| Sessions | `POST /sessions/{session_id}/summarize` | Force session summarization |
| Memory | `GET /memory/{session_id}/short-term` | Retrieve relevant session memory context |
| Memory | `GET /memory/long-term` | Retrieve relevant long-term memory context |
| Memory | `POST /memory/{session_id}/summarize` | Trigger memory summarization |
| Sources | `GET /sources/{session_id}` | List sources for a session |

## Setup

### 1. Create environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure `.env`

```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
TAVILY_API_KEY=your_key
TAVILY_BASE_URL=https://api.tavily.com
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/meridian
CHROMA_PATH=chroma_data
EMBEDDING_MODEL=openai/text-embedding-3-small
SUMMARY_MODEL=openai/gpt-4o-mini
RESEARCH_MODEL=openai/gpt-4o-mini
MIN_MESSAGES_FOR_AUTO_SUMMARIZE=5
```

### 3. Start Postgres

```bash
docker compose up -d
```

Apply the initial schema:

```bash
docker exec -i meridian-postgres psql -U postgres -d meridian < app/db/migrations/001_initial_schema.sql
```

### 4. Start backend

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Backend health check:

```text
http://127.0.0.1:8000/health
```

### 5. Start frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5174
```

Open:

```text
http://127.0.0.1:5174/
```

### 6. Run memory worker

Run this in a separate terminal when testing long-term memory summarization:

```bash
.venv/bin/python scripts/run_worker.py
```

## Testing

Backend tests:

```bash
pytest tests/
```

Frontend production build:

```bash
cd frontend
npm run build
```

Expected backend test result:

```text
19 passed
```

## Frontend Notes

- Normal mode uses a blue/aqua dark theme.
- Deep mode uses a purple/indigo dark theme.
- Mobile layout hides token counters, moves citations/sources to the bottom, and keeps history inside a dropdown.
- The response panel renders markdown headings, lists, inline code, and fenced code blocks.
- The response box scrolls internally so long answers do not break the page layout.

## Project Status

The planned research, memory, source tracking, citation, WebSocket, and integration phases are complete and covered by tests. Remaining improvements are product polish items such as richer source quality scoring, uploaded document support, report export, and a dedicated memory management UI.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
