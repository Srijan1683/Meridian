from openai import AsyncOpenAI
import tiktoken

from app.config import settings


MAX_EMBEDDING_TOKENS = 8191
CHUNK_OVERLAP_TOKENS = 100

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


def _get_encoding():
    return tiktoken.get_encoding("cl100k_base")


def _chunk_text(text: str, max_tokens: int = MAX_EMBEDDING_TOKENS) -> list[str]:
    encoding = _get_encoding()
    tokens = encoding.encode(text)

    if len(tokens) <= max_tokens:
        return [text]

    chunks: list[str] = []
    start = 0
    step = max_tokens - CHUNK_OVERLAP_TOKENS

    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        chunks.append(encoding.decode(chunk_tokens))
        start += step

    return chunks


def _average_embeddings(embeddings: list[list[float]]) -> list[float]:
    if not embeddings:
        return []

    embedding_length = len(embeddings[0])
    averaged: list[float] = []

    for index in range(embedding_length):
        value = sum(embedding[index] for embedding in embeddings) / len(embeddings)
        averaged.append(value)

    return averaged


async def _embed_without_chunking(text: str) -> list[float]:
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )

    return response.data[0].embedding


async def embed_text(text: str) -> list[float]:
    chunks = _chunk_text(text)

    if len(chunks) == 1:
        return await _embed_without_chunking(chunks[0])

    chunk_embeddings = await embed_texts(chunks)
    return _average_embeddings(chunk_embeddings)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    all_embeddings: list[list[float]] = []

    for text in texts:
        chunks = _chunk_text(text)

        if len(chunks) == 1:
            embedding = await _embed_without_chunking(chunks[0])
            all_embeddings.append(embedding)
            continue

        chunk_embeddings = await embed_texts(chunks)
        all_embeddings.append(_average_embeddings(chunk_embeddings))

    return all_embeddings
