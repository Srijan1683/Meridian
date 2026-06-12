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

Meridian is built around a FastAPI server with routes for research, sessions, memory, sources, and WebSocket streaming.

The research agent is a single mode-driven agent. Normal mode prioritizes quick answers, while deep mode prioritizes thorough iterative research. Both modes use memory retrieval, session history, token budgeting, web search, and source tracking.

The memory system uses ChromaDB for semantic retrieval and PostgreSQL for structured persistence. Background workers summarize completed sessions and store long-term memories for future recall.

## Research Flow

### Deep Research

In deep research mode, the agent retrieves short-term and long-term memory, searches from multiple angles, evaluates sources, runs follow-up searches, and synthesizes a cited answer. The response can be streamed over WebSocket while messages, sources, citations, and memory artifacts are stored in the background.

### Normal Research

In normal mode, the agent retrieves relevant memory, runs one or two searches, returns a concise cited answer, and stores the interaction in short-term memory.

## ChromaDB Collections

### Short-Term Memory

Stores the user query and assistant response for a session.

Metadata includes:

- session identifiers
- message identifiers
- timestamps
- topic tags

### Long-Term Memory

Stores session summaries that can be recalled across future sessions.

Metadata includes:

- session identifiers
- key topics
- key findings
- summarization timestamps

## API Endpoints

### Research

| Endpoint | Description |
| --- | --- |
| Research endpoint | Submit a non-streaming research query. |
| WebSocket research endpoint | Run streaming research with progress events. |

### Memory

| Endpoint | Description |
| --- | --- |
| Session memory endpoint | Get relevant memory context for a session. |
| Long-term memory endpoint | Query long-term memory across sessions. |
| Memory jobs endpoint | List memory summarization jobs. |
| Manual memory job endpoint | Manually trigger memory summarization. |

### Sources

| Endpoint | Description |
| --- | --- |
| Session sources endpoint | Return all sources found during a session. |

## Implementation Plan

### Phase 1: ChromaDB Setup and Embedding Pipeline

Set up ChromaDB in persistent mode, create short-term and long-term collections, and build an embedding service.

Key tasks:

- Implement single-text embedding.
- Implement batch embedding.
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

Use inline citation markers in the response text, then include a source list at the end.

Store citation mappings in Postgres:

- citation index
- source identifier
- claim text

The system should validate that every citation marker maps to a real source.

### Phase 7: WebSocket Streaming

Use a WebSocket endpoint for streaming research progress.

Expected event flow: searching, content, source, memory, then done.

The client can send a cancel event to stop research mid-stream.

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
