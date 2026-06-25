CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Sessions table
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'ended')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT NOT NULL DEFAULT 0
);

CREATE INDEX idx_sessions_updated_at ON sessions(updated_at DESC);
CREATE INDEX idx_sessions_status ON sessions(status);

-- Conversation history
CREATE TABLE conversation_history (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_history_session ON conversation_history(session_id, created_at);

-- Tool call log
CREATE TABLE tool_call_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    message_id UUID REFERENCES conversation_history(message_id),
    tool_name TEXT NOT NULL,
    input_args JSONB NOT NULL,
    output_summary TEXT,
    duration_ms INT,
    cached BOOLEAN NOT NULL DEFAULT FALSE,
    called_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_session ON tool_call_log(session_id, called_at);
CREATE INDEX idx_tool_calls_tool ON tool_call_log(tool_name);

-- API usage tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status_code INT NOT NULL,
    response_time_ms INT,
    rate_limit_remaining INT,
    rate_limit_reset_at TIMESTAMPTZ,
    called_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_usage_name ON api_usage(api_name, called_at DESC);

-- Cached API responses
CREATE TABLE cached_api_responses (
    cache_key TEXT PRIMARY KEY,
    api_name TEXT NOT NULL,
    query TEXT NOT NULL,
    response_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_cache_expires ON cached_api_responses(expires_at);

-- Sources — every piece of information the agent found
CREATE TABLE sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('web', 'paper', 'article', 'forum', 'documentation')),
    search_query TEXT NOT NULL,
    credibility_note TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sources_session ON sources(session_id);
CREATE INDEX idx_sources_url ON sources(url);

-- Memory summarization jobs
CREATE TABLE memory_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('queued', 'summarizing', 'embedding', 'completed', 'failed')),
    summary TEXT,
    key_topics TEXT[],
    key_findings TEXT[],
    sources_referenced TEXT[],
    unresolved_questions TEXT[],
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX idx_memory_jobs_status ON memory_jobs(status);
CREATE INDEX idx_memory_jobs_session ON memory_jobs(session_id);

-- Source citations — links sources to claims in responses
CREATE TABLE source_citations (
    citation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES conversation_history(message_id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES sources(source_id),
    citation_index INT NOT NULL,
    claim_text TEXT NOT NULL
);

CREATE INDEX idx_citations_message ON source_citations(message_id);
