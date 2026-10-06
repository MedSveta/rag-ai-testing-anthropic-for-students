# Architecture — v0.3.0

```mermaid
flowchart TD
    A[knowledge/requirements.md] --> B[Requirement-aware Markdown chunker]
    B --> C[Local sentence-transformer embeddings]
    C --> D[(ChromaDB)]
    M[index manifest: KB hash + embedding model + chunker version] --> D
    Q[POST /ask question] --> E[Retriever]
    D --> E
    E --> T{score >= threshold?}
    T -- no --> N[Deterministic "not specified" answer\nNo Anthropic call]
    T -- yes --> F[Retrieved contexts]
    F --> G[Prompt builder]
    Q --> G
    G --> H[Claude via Anthropic API]
    H --> I[Answer + token usage]
```

## Knowledge base contains product knowledge only

`knowledge/requirements.md` contains product knowledge only. Test questions and expected answers must be kept outside the knowledge base.

This prevents **evaluation-data leakage**: a test question must never become a retrievable knowledge chunk. As a safeguard, the chunker also skips any section titled `Suggested RAG Test Questions`.

Source-quality observations are kept in `docs/SOURCE_NOTES.md`, which is not indexed.

## Requirement-level chunking

Technical and functional requirements such as `T14`, `T15`, and `F8` are emitted as atomic chunks. A query about maximum password length can therefore retrieve `T15` directly instead of a large section containing every password rule.

General prose is still chunked by heading and paragraph.

## Why the project exposes `/retrieve`

RAG failures can happen before the LLM is called. `/retrieve` lets QA inspect the selected chunks, requirement IDs and similarity scores without paying for an LLM request.

## Relevance threshold

The retriever filters candidates using `MIN_RELEVANCE_SCORE`. If no chunk clears the threshold, `/ask` returns the fixed missing-information response without calling Anthropic.

A related-but-unanswered question can still retrieve topically related context. In that case Claude must follow the system prompt and refuse to invent a requirement.

## Automatic index invalidation

The `.chroma` directory contains an index manifest with:

- SHA-256 of the knowledge file;
- embedding model name;
- chunker version;
- collection name.

If any of those change, `AUTO_INDEX=true` rebuilds the collection automatically. This prevents stale answers after editing the Markdown requirements or changing the embedding model.

## Why LangChain is intentionally absent

The training version keeps chunking, embedding, retrieval, prompt construction and generation visible in project code. This makes component-level testing easier to teach. A later branch can introduce LangChain and compare architectures.
