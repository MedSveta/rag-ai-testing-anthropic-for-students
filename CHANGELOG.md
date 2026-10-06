# Changelog

## 0.3.0

### Removed

- Golden Dataset, retrieval/AI/DeepEval tests and DeepEval settings. QA-level tests are written in the course.

### Added

- Developer unit test suite in `tests/unit/` for every module in `app/` and `scripts/` (no API key, no model download, no network).

## 0.2.0

Code-review hardening release.

### Fixed

- Removed evaluation questions and instructor notes from the indexed knowledge base.
- Added defence-in-depth subtree exclusion in the Markdown chunker.
- Switched `T*`/`F*` requirements to atomic requirement-level chunks.
- Added a retrieval relevance threshold.
- Added deterministic no-context behavior that avoids an unnecessary Anthropic call.
- Added an index manifest based on knowledge SHA-256, embedding model and chunker version; stale indexes are rebuilt automatically.
- Recreate the Chroma collection during reindexing so embedding-dimension changes cannot reuse an incompatible collection.
- Added provider-specific Anthropic error mapping for authentication, rate limits, timeouts, connection errors and API failures.
- Added `pyproject.toml` and package/console-script entry points.
- Changed documented script execution to module/console commands.

### Added

- `docs/SOURCE_NOTES.md` for non-indexed source-quality observations.
