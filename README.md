# Meridian

Meridian is a deep research agent with memory. It can answer quick lookup questions in one pass, or run a deeper iterative research flow that searches from multiple angles, evaluates sources, identifies gaps, and synthesizes a cited answer.

The core feature is memory:

- **Short-term memory:** session-level semantic memory stored in a vector database.
- **Long-term memory:** cross-session summaries generated asynchronously and retrieved in future sessions.

This project brings together agent orchestration, web search, citations, vector databases, RAG, WebSocket streaming, background jobs, and persistent session storage.

## Research Modes

### Normal Mode

Normal mode is for quick questions. The agent performs one or two searches, reads the results, and returns a concise answer with citations.

### Deep Research Mode

Deep research mode is for complex questions. The agent:

1. Breaks the question into research angles.
2. Searches iteratively.
3. Evaluates sources.
4. Finds gaps and contradictions.
5. Runs follow-up searches.
6. Synthesizes a comprehensive answer with inline citations.

Both modes use the same agent architecture. The difference is the system prompt and expected depth.

## What This Project Covers

| Skill | Why it matters |
| --- | --- |
| Vector databases | Store embeddings and retrieve semantically relevant memory. |
| RAG | Retrieve useful context before generation. |
| Memory systems | Support both session-level and cross-session recall. |
| Async summarization pipelines | Generate durable knowledge artifacts in the background. |
| Web search integration | Let the agent investigate open-ended questions. |
| Source tracking and citations | Make claims traceable to their sources. |
| WebSocket streaming | Stream research progress and support cancellation. |

Reused concepts from earlier projects include FastAPI, async Python, Postgres, asyncpg, OpenAI Agents SDK, tool calling, session management, token counting, rate limits, Pydantic, and httpx.

New concepts include ChromaDB, embedding models, RAG pipelines, WebSockets, Perplexity API integration, and memory summarization workers.

## Tech Stack

| Library | Purpose |
| --- | --- |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| openai-agents | Agent orchestration and tool calling |
| openai | LLM calls and embedding generation |
| asyncpg | Async Postgres driver |
| ChromaDB | Vector database for memory and RAG |
| httpx | Async HTTP client |
| tiktoken | Token counting |
| Pydantic | Data models |
| python-dotenv | Environment variables |

## External APIs

| API | Purpose |
| --- | --- |
| Perplexity API | Web search over the open internet |
| OpenAI API | Agent reasoning, summarization, and embeddings |

## Architecture

```text
┌──────────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                               │
│                                                                      │
│  [Research Routes]  [Session Routes]  [Memory Routes]  [WebSocket]  │
│         │                 │                 │                │       │
│  ┌──────┴─────────────────┴─────────────────┴────────────────┴────┐ │
│  │                  Agent (single, mode-driven)                    │ │
│  │                                                                  │ │
│  │  Normal mode: quick search and answer                           │ │
│  │  Deep mode: iterative research with citations                   │ │
│  │                                                                  │ │
│  │  Tools: Perplexity web search                                   │ │
│  │  Context: memory retrieval, session history, token budget        │ │
│  └──────────────────────────────┬───────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────┴──────────────────────────────────┐ │
│  │                         Memory Manager                          │ │
│  │  ┌─────────────────────┐  ┌──────────────────────────────────┐  │ │
│  │  │ Short-term memory   │  │ Long-term memory                 │  │ │
│  │  │ per-session vector  │  │ cross-session summaries          │  │ │
│  │  │ storage             │  │ vector storage                   │  │ │
│  │  └─────────────────────┘  └──────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ChromaDB: short_term_{session_id}, long_term_memory                 │
│  PostgreSQL: sessions, messages, sources, citations, memory_jobs     │
│  Background workers: summarization and memory consolidation          │
└──────────────────────────────────────────────────────────────────────┘
```

## Research Flow

### Deep Research

```text
User asks a complex question
  │
  ├─ Mode: deep research
  ├─ Retrieve short-term and long-term memory
  ├─ Build agent context from query, memory, history, and token budget
  ├─ Search from multiple angles
  ├─ Evaluate agreement, disagreement, and gaps
  ├─ Run follow-up searches
  ├─ Synthesize answer with inline citations
  ├─ Stream progress over WebSocket
  └─ Store messages, sources, citations, and memory artifacts
```

### Normal Research

```text
User asks a straightforward question
  │
  ├─ Mode: normal
  ├─ Retrieve relevant memory
  ├─ Run one or two searches
  ├─ Return a concise cited answer
  └─ Store the interaction in short-term memory
```

## Data Models

### Research Models

```python
class ResearchMode(str, Enum):
    NORMAL = "normal"
    DEEP = "deep"


class ResearchRequest(BaseModel):
    session_id: UUID | None = None
    query: str
    mode: ResearchMode = ResearchMode.NORMAL


class Source(BaseModel):
    source_id: UUID
    url: str
    title: str
    snippet: str
    source_type: Literal["web", "paper", "article", "forum", "documentation"]
    retrieved_at: datetime
    search_query: str
    credibility_note: str | None = None


class ResearchResponse(BaseModel):
    session_id: UUID
    mode: ResearchMode
    response: str
    sources: list[Source]
    memory_context: MemoryContext
    token_usage: TokenBudget
```

### Memory Models

```python
class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"


class MemoryEntry(BaseModel):
    memory_id: UUID
    memory_type: MemoryType
    session_id: UUID
    content: str
    metadata: dict
    similarity_score: float | None = None
    created_at: datetime


class MemoryContext(BaseModel):
    short_term_retrieved: int
    long_term_retrieved: int
    memories: list[MemoryEntry]
    retrieval_time_ms: int


class SessionSummary(BaseModel):
    session_id: UUID
    summary: str
    key_topics: list[str]
    key_findings: list[str]
    sources_referenced: list[str]
    generated_at: datetime


class MemoryJobStatus(BaseModel):
    job_id: UUID
    session_id: UUID
    status: Literal["queued", "summarizing", "embedding", "completed", "failed"]
    created_at: datetime
    completed_at: datetime | None = None
```

### WebSocket Models

```python
class WSMessageType(str, Enum):
    QUERY = "query"
    CANCEL = "cancel"
    SEARCHING = "searching"
    CONTENT = "content"
    SOURCE = "source"
    MEMORY = "memory"
    DONE = "done"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict
    timestamp: datetime
```

## Database Schema

```sql
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT NOT NULL,
    source_type TEXT NOT NULL,
    search_query TEXT NOT NULL,
    credibility_note TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sources_session ON sources(session_id);
CREATE INDEX idx_sources_url ON sources(url);

CREATE TABLE memory_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (
        status IN ('queued', 'summarizing', 'embedding', 'completed', 'failed')
    ),
    summary TEXT,
    key_topics TEXT[],
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_memory_jobs_status ON memory_jobs(status);

CREATE TABLE source_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES conversation_history(message_id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(source_id),
    citation_index INT NOT NULL,
    claim_text TEXT NOT NULL
);

CREATE INDEX idx_citations_message ON source_citations(message_id);
```

## ChromaDB Collections

### Short-Term Memory

```python
short_term = chroma_client.get_or_create_collection(
    name=f"short_term_{session_id}",
    metadata={"hnsw:space": "cosine"},
)
```

Stores the user query and assistant response for a session.

Metadata includes:

- `session_id`
- `message_id`
- `timestamp`
- `topic_tags`

### Long-Term Memory

```python
long_term = chroma_client.get_or_create_collection(
    name="long_term_memory",
    metadata={"hnsw:space": "cosine"},
)
```

Stores session summaries that can be recalled across future sessions.

Metadata includes:

- `session_id`
- `key_topics`
- `key_findings`
- `summarized_at`

## API Endpoints

### Research

| Endpoint | Description |
| --- | --- |
| `POST /research` | Submit a non-streaming research query. |
| `WebSocket /ws/research` | Run streaming research with progress events. |

Example WebSocket query:

```json
{
  "type": "query",
  "data": {
    "query": "What are the leading theories on consciousness?",
    "mode": "deep",
    "session_id": "..."
  }
}
```

### Memory

| Endpoint | Description |
| --- | --- |
| `GET /sessions/{session_id}/memory` | Get relevant memory context for a session. |
| `GET /memory/long-term` | Query long-term memory across sessions. |
| `GET /memory/jobs` | List memory summarization jobs. |
| `POST /memory/jobs/{session_id}` | Manually trigger memory summarization. |

### Sources

| Endpoint | Description |
| --- | --- |
| `GET /sessions/{session_id}/sources` | Return all sources found during a session. |

## Implementation Plan

### Phase 1: ChromaDB Setup and Embedding Pipeline

Set up ChromaDB in persistent mode, create short-term and long-term collections, and build an embedding service using `text-embedding-3-small`.

Key tasks:

- Implement `embed_text(text) -> list[float]`.
- Implement `embed_texts(texts) -> list[list[float]]`.
- Chunk long text before embedding.
- Build similarity retrieval with a relevance threshold.
- Test semantic retrieval with unrelated and related paragraphs.

### Phase 2: Short-Term Memory

Store every query-response pair in the session's short-term collection. Before each new query, retrieve semantically relevant context from the current session.

This lets the agent reference relevant older messages even if they are no longer in the recent conversation window.

### Phase 3: Long-Term Memory and Async Summarization

When a session ends, create a background memory job that:

1. Loads all session messages.
2. Summarizes the session.
3. Extracts topics, findings, sources, and unresolved questions.
4. Embeds the summary.
5. Stores it in the long-term memory collection.
6. Updates the job status.

Only sessions with enough substance should be summarized automatically. Short sessions can be summarized manually through the API.

### Phase 4: Perplexity Web Search Integration

Integrate Perplexity as the agent's web search tool. Store every returned source in Postgres with the query that found it.

Deep mode should encourage the agent to create multiple targeted searches rather than repeating the user's original question.

### Phase 5: Two Research Modes

Use one agent with mode-specific prompting:

- **Normal:** concise answer, one or two searches, citations required.
- **Deep:** investigate multiple angles, iterate, resolve gaps, cite every factual claim.

### Phase 6: Citation and Source System

Use inline citation markers such as `[1]` and `[2]` in the response text, then include a source list at the end.

Store citation mappings in Postgres:

- `citation_index`
- `source_id`
- `claim_text`

The system should validate that every citation marker maps to a real source.

### Phase 7: WebSocket Streaming

Use `ws://localhost:8000/ws/research` for streaming research progress.

Expected event flow:

```text
searching -> content -> source -> memory -> done
```

The client can send a cancel event:

```json
{ "type": "cancel" }
```

If the client disconnects, research can continue in the background and store results for later retrieval.

### Phase 8: End-to-End Integration

Test the full flow:

- Normal research query.
- Deep research query over WebSocket.
- Source tracking.
- Citation validation.
- Short-term memory retrieval.
- Long-term memory retrieval after session summarization.
- Edge cases such as rate limits, long sessions, and disconnections.

## Key Concepts

### Memory Architecture

Short-term memory solves the context window problem better than simple truncation. Instead of keeping only the most recent messages, the system retrieves the most semantically relevant interactions from the session.

Long-term memory solves the session boundary problem. It lets the agent recall what was researched in previous sessions and use that context in future conversations.

### Vector Search

Embeddings convert text into points in a high-dimensional space. Similar meanings are close together, which allows the system to retrieve relevant memories even when the wording is different.

Important considerations:

- Focused chunks produce better embeddings than large unfocused documents.
- Similarity thresholds prevent weakly related memories from polluting the prompt.
- Metadata filtering keeps retrieval scoped to the right session, time period, or memory type.

### WebSocket vs SSE

Server-Sent Events are one-way. WebSockets are bidirectional, which makes them a better fit here because the server streams research progress while the client can cancel or send follow-up messages on the same connection.

### Single-Agent Design

Meridian intentionally uses one mode-driven agent instead of a planner-executor-synthesizer system. Modern LLMs can handle planning, searching, evaluating, and synthesizing inside one tool-calling loop.

This keeps the architecture focused on the hard parts: memory, citations, retrieval, and infrastructure.

## Stretch Goals

- Export deep research sessions as formatted reports.
- Build a memory management UI.
- Support collaborative research sessions.
- Add source quality scoring.
- Compare research results for the same question over time.
- Support uploaded personal documents as a custom knowledge base.
- Experiment with a multi-agent research architecture.
