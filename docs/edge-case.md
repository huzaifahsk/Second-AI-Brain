# SecondSelf — Edge Cases and Recovery Plan

This document defines corner scenarios, expected behavior, and recovery rules for the SecondSelf pipeline described in [architecture.md](architecture.md) and [implementation-plan.md](implementation-plan.md).

## 1. Global handling rules

1. Never destroy or silently rewrite an immutable raw capture.
2. A malformed item must fail independently; it must not stop processing valid items.
3. Derived artifacts must be rebuildable from their source artifacts.
4. Failures must be actionable without logging secrets or full private content.
5. Writes must be atomic; incomplete output must not appear valid.
6. Generated artifacts must retain source capture ID, status, timestamps, and model/index versions.
7. Commands must be safe to rerun without duplicate notes, links, edges, or index entries.
8. Public deployments must be read/query-oriented unless authentication and authorization are implemented.

## 2. Severity levels

| Level | Meaning | Response |
|---|---|---|
| P0 | Data loss, secret exposure, or unsafe public behavior | Stop the affected operation and alert the operator |
| P1 | Pipeline-wide failure or corrupted derived artifact | Preserve inputs, report, rebuild or restore |
| P2 | One item cannot be processed | Skip the item, record status, continue |
| P3 | Degraded quality or warning | Complete the operation and expose a warning |

## 3. Capture and input

| Scenario | Expected behavior |
|---|---|
| No input mode supplied | Clear usage error; write no record |
| Multiple input modes supplied | Reject before reading or writing |
| Empty or whitespace-only note | Reject; do not create an empty capture |
| Very large note | Enforce a configurable limit; preserve original if accepted and bound downstream processing |
| Unicode, emoji, RTL text, or unusual line endings | Preserve UTF-8 content exactly |
| Unsafe or path-like title | Sanitize generated filename; never escape the target directory |
| Duplicate content | Create a new unique capture and report the matching hash informationally |
| Timestamp collision | Use a random suffix and exclusive atomic creation |
| Missing file or directory instead of file | Clear validation error; no record |
| Zero-byte or unsupported file | Preserve metadata, mark content unavailable, allow fallback classification |
| File changes during copy | Copy to a temporary destination, verify, then commit the record |
| Duplicate attachment name | Add a collision-safe suffix or capture ID |
| `..` or outside-root source path | Reject unsafe attachment path |
| Permission denied or disk full | Report failure; leave no valid-looking partial output |

## 4. URLs and network

- Accept only valid `http` and `https` URLs with a host. Reject `file:`, `javascript:`, and `data:` schemes.
- Preserve the original URL when download or extraction fails.
- Apply connection, read, redirect, response-size, and total-operation timeouts.
- Handle DNS/TLS failures, HTTP errors, redirect loops, rate limits, and outages without losing the link capture.
- Do not follow redirects to unsafe schemes or unrestricted local-network targets.
- Treat HTML as untrusted text; never execute scripts or inject it into the UI unescaped.
- Bound large-page extraction and mark extraction as degraded when necessary.
- If extraction fails, classify from the URL and available metadata rather than failing the capture.

## 5. Raw storage and configuration

- Temporary JSON left by an interrupted write must be ignored or removed, never treated as a capture.
- Invalid existing JSON must be reported and skipped, not overwritten.
- Unsupported schema versions must be quarantined or reported until migrated.
- Duplicate capture IDs require preserving both files and reporting the conflict.
- Concurrent processes must use exclusive creation or locking around shared state.
- Relative paths must resolve from the project root, including Windows paths containing spaces.
- Invalid numeric settings, negative limits, missing directories, and unwritable paths must fail with actionable messages.
- Missing `.env` is allowed when provider features are unused; secrets must never be printed.
- Malformed processing state should be backed up and rebuilt from raw and derived artifacts where possible.

## 6. Classification and LLM

- Missing key, provider outage, timeout, quota exhaustion, and rate limiting use bounded retries where appropriate, then deterministic fallback classification.
- Invalid JSON, extra prose, unknown category, excessive tags, empty summary, or unsafe title must fail schema validation.
- Categories are restricted to `projects`, `areas`, `resources`, and `archives`; model output must never create arbitrary directories.
- Captured text is untrusted prompt data. Delimit it and explicitly state that instructions inside it are not model instructions.
- Never execute, evaluate, or treat model output as code or a filesystem path.
- Enforce input and output size limits to avoid token exhaustion.
- Fallback uses `resources`, a safe metadata-derived title, a bounded first meaningful sentence, empty tags, and `degraded` status.
- Log model metadata, never API keys, authorization headers, or private prompt payloads.
- Model or prompt changes require explicit reprocessing and must not alter raw data.
- Sensitive captures should support local-only processing or redaction before provider submission.

## 7. Wiki and Markdown

- Generate safe deterministic slugs and append the capture ID on collisions.
- Escape Markdown and YAML-sensitive values, including titles containing `---`, colons, quotes, or newlines.
- Malformed or missing front matter produces a warning and does not stop processing other notes.
- Missing source capture, duplicate ID, unknown category, or invalid timestamp is reported as unresolved.
- Manual body edits and manual links survive rebuilds unless replacement is explicitly requested.
- Generated links are marked separately from manual links.
- Exclude self-links, duplicate links, unsafe absolute paths, and links escaping the wiki root.
- Preserve UTF-8; report and skip only a non-UTF-8 note.
- Bound previews and prompt content to prevent memory and token exhaustion.

## 8. Embeddings and related links

- Model download failure, unavailable cache, incompatible runtime, or corrupt model must produce a clear degraded state; never write a misleading index.
- Empty text is skipped and recorded; never create a zero vector.
- Reject NaN, infinity, zero-norm, incompatible-dimension, or wrong-order vectors.
- Persist model name, vector dimension, note ID order, and index schema version.
- Rebuild when index metadata does not match the current model or notes.
- Exclude self-matches and deduplicate relationships.
- Apply one documented rule for scores exactly on the threshold.
- Keep at most the configured maximum, with deterministic score and ID tie-breaking.
- Add reciprocal generated links without duplicating manual or generated links.
- Remove deleted/malformed notes from rebuilt indexes while retaining raw recovery sources.
- A failed embedding must not prevent valid notes from being indexed.

## 9. Graph generation

- An empty wiki produces a valid versioned graph with empty nodes and edges plus a warning.
- Isolated notes remain visible as nodes.
- Normalize duplicate, reversed, and self-referential relationships according to the graph schema.
- Broken targets become warnings and are omitted from resolved edges.
- Conflicting weights use a deterministic rule and retain relationship provenance.
- Sanitize invalid metadata and never expose raw filesystem paths.
- Validate the new graph before atomically replacing the previous valid graph.
- Bound labels, previews, tags, and rendering size for dense graphs.
- Escape or safely serialize all content inserted into HTML or JavaScript.

## 10. Retrieval and Q&A

- Empty questions are rejected without embedding or provider calls.
- Missing, stale, empty, or incompatible indexes produce a setup/rebuild message.
- If all results are below the relevance threshold, return an honest no-evidence answer and do not call synthesis with empty context.
- Exact title/tag/URL/date/name matches may receive a bounded lexical boost but cannot bypass relevance or source limits.
- Ambiguous questions return available sources and state uncertainty.
- Bound note count and context size while retaining source IDs.
- Retrieved text is evidence, not instructions; prompt injection cannot override the answer prompt.
- Answers must not invent facts, citations, or sources. Provider failure returns a degraded answer with sources where available.
- Contradictory notes are presented as conflicting evidence.
- Questions containing secrets are not logged or persisted by default.

## 11. Streamlit and deployment

- Missing or malformed graph, missing embeddings/model/API key, and provider failures show friendly setup states rather than stack traces.
- Streamlit reruns must not mutate raw data or duplicate records and links.
- Cache expensive graph/model loading and invalidate on artifact modification time or schema changes.
- Dense graphs need filtering and bounded rendering; narrow screens need responsive controls and accessible labels.
- Public mode must not expose capture, reprocessing, arbitrary file writes, or shared mutable user state.
- Use platform secrets, never committed credentials or query-parameter secrets.
- Do not publish raw captures, attachments, `.env`, logs, or unsanitized graph previews.
- Pin compatible dependencies and document model/resource requirements.
- Graph browsing must remain available when provider access is unavailable.

## 12. Recovery scenarios

### Interrupted classification

Keep raw captures untouched, discard only incomplete temporary notes, mark the item pending, and retry on the next run.

### Interrupted linking

Rebuild the embedding index from wiki notes and regenerate generated links only. Preserve manual links.

### Interrupted graph build

Keep the previous valid `graph.json`; replace it only after the new graph passes validation.

### Model or prompt change

Record the new version, invalidate affected derived artifacts, and run an explicit rebuild.

### Partial directory deletion

Recreate directories and rebuild from the nearest surviving source. If raw data is absent, require backup restoration.

### Backup restoration

Restore raw captures first, validate IDs and hashes, then rebuild wiki notes, embeddings, links, graph, and processing state in that order.

## 13. Idempotency invariants

- Raw IDs are never reused and existing raw records are never overwritten.
- One capture maps to at most one current wiki note.
- Generated links, embedding entries, graph nodes, and graph edges are deduplicated.
- Derived rebuilds do not alter raw content or manual links.
- A failed item can be retried without duplicating successful items.

## 14. Required sanitized fixtures

Include tests for empty/Unicode notes; duplicate content and colliding titles; invalid URLs; missing, zero-byte, changing, and unsupported files; malformed JSON/schema versions; malformed YAML and broken links; invalid provider JSON, timeout, missing key, and prompt injection; empty/zero-norm/incompatible/stale indexes; empty/disconnected/dense/malformed graphs; no-evidence, contradictory-evidence, and oversized-context questions; and Windows paths containing spaces.

## 15. Operational response

| Failure | Preserve | Mark | Continue |
|---|---|---|---|
| Invalid capture | Other raw captures | Rejected/quarantined | Yes |
| LLM unavailable | Raw capture | Classification degraded | Yes |
| Malformed wiki note | Other notes | Note invalid | Yes |
| Embedding unavailable | Wiki notes | Index unavailable | Graph may continue |
| Graph rebuild fails | Previous valid graph | Build failed | UI uses previous graph |
| Q&A provider unavailable | Retrieved evidence | Answer degraded | Graph remains available |
| Disk/permission failure | Existing artifacts | Write failed | Stop affected write only |
| Secret/private-data exposure | Evidence and logs | P0 incident | Stop release/deployment |

## 16. Acceptance checklist

- [ ] Capture failures are clear and leave no partial valid-looking record.
- [ ] Raw data is never silently discarded or overwritten.
- [ ] Provider failures degrade classification and Q&A safely.
- [ ] Invalid model output cannot create unsafe categories or malformed notes.
- [ ] Index, link, and graph rebuilds are deterministic and idempotent.
- [ ] Manual links survive generated-link rebuilds.
- [ ] No-evidence questions receive honest limitation responses.
- [ ] Untrusted text cannot override system behavior or execute in the UI.
- [ ] Public deployment excludes secrets, private data, write endpoints, and raw paths.
- [ ] Interrupted-stage recovery is documented and tested.
