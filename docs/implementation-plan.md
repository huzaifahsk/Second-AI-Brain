# SecondSelf — Phase-Wise Implementation Plan

This plan converts the project brief and [architecture.md](architecture.md) into an incremental implementation sequence. Each phase produces a usable artifact, has explicit dependencies, and ends with verification before the next phase begins.

## 1. Delivery strategy

### Product milestones

| Milestone | Phases | Outcome |
|---|---:|---|
| The Archivist | 0–2 | A reliable capture pipeline with real raw data |
| The Librarian | 3–4 | PARA-organized notes with embeddings and automatic links |
| The Cartographer | 5–6 | A generated and interactive knowledge graph |
| The Oracle | 7–9 | Retrieval-augmented Q&A and a deployable public app |

### Implementation rules

- Keep `raw/` immutable; all later stages create or update derived artifacts.
- Make every command rerunnable and idempotent.
- Use real personal information for milestone validation, not only fixtures.
- Keep external provider access behind interfaces so providers can be replaced.
- Do not commit API keys, private secrets, or sensitive personal notes to a public repository.
- Validate each phase before beginning the next one.

## 2. Target repository structure

```text
Your Second AI Brain/
├── raw/
│   └── attachments/
├── wiki/
│   ├── projects/
│   ├── areas/
│   ├── resources/
│   └── archives/
├── data/
├── static/
├── tests/
├── docs/
├── capture.py
├── classify.py
├── link.py
├── build_graph.py
├── ask.py
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── architecture.md
└── implementation-plan.md
```

The documentation may remain at the project root as requested. The `docs/` directory is reserved for the problem statement and future edge-case documentation.

## 3. Phase 0 — Project setup and foundations

### Objective

Create a reproducible Python project with the directory structure, configuration conventions, dependency management, and shared data contracts required by every later phase.

### Tasks

1. Create the required directories:
   - `raw/`
   - `raw/attachments/`
   - `wiki/projects/`
   - `wiki/areas/`
   - `wiki/resources/`
   - `wiki/archives/`
   - `data/`
   - `static/`
   - `tests/`
   - `docs/`
2. Create `requirements.txt` with initially required packages:
   - `streamlit`
   - `sentence-transformers`
   - `numpy`
   - `pydantic`
   - `python-dotenv`
   - `requests`
   - `PyYAML`
   - graph rendering dependency selected during Phase 6
   - optional file-extraction dependencies selected during Phase 2
3. Create `.gitignore` for:
   - `.env`
   - virtual environments
   - Python caches
   - generated embedding data if not intended for version control
   - private raw attachments
   - editor and operating-system files
4. Create `.env.example` with documented non-secret settings.
5. Define shared configuration values and path resolution relative to the project root.
6. Define typed contracts for:
   - `CaptureRecord`
   - `Classification`
   - `WikiNote`
   - `RelatedNote`
   - `RetrievedNote`
   - `Answer`
7. Add a basic logging convention containing stage, capture ID, and status without logging secrets or full private content.
8. Write the initial `README.md` with local setup, environment configuration, and planned commands.

### Deliverables

- Reproducible project skeleton.
- Dependency and environment configuration.
- Shared schemas and path configuration.
- Initial README.

### Verification

- A fresh virtual environment installs dependencies successfully.
- All required directories exist.
- Importing shared configuration and schemas succeeds.
- `.env` and private data are excluded from version control.
- Running the project from a path containing spaces works on Windows.

### Exit criteria

Phase 0 is complete when a clean checkout can be initialized without manual file creation beyond the environment secrets.

## 4. Phase 1 — Capture data model and storage layer

### Objective

Implement the immutable raw repository and safe file-writing utilities before exposing the command-line interface.

### Tasks

1. Implement a UTC timestamp generator using ISO 8601 format.
2. Implement collision-resistant capture IDs in the form:
   `cap_<UTC timestamp>_<random suffix>`.
3. Implement SHA-256 hashing for captured content.
4. Implement atomic JSON writes using a temporary file and rename.
5. Implement raw-record validation:
   - valid ID;
   - supported type: `note`, `link`, or `file`;
   - non-empty content or source;
   - valid timestamp;
   - safe attachment path;
   - schema version.
6. Implement duplicate detection as an informational result based on content hash; never discard the new capture silently.
7. Implement file-copy behavior into `raw/attachments/` with a collision-safe destination filename.
8. Add unit tests for schemas, timestamps, IDs, hashing, path safety, atomic writes, and duplicate detection.

### Deliverables

- Raw capture schema and storage utilities.
- Immutable JSON records under `raw/`.
- Safe attachment-copy mechanism.
- Unit tests for the storage layer.

### Verification

- A raw record can be written and read back without data loss.
- Existing records are never overwritten.
- Attachment paths cannot escape the configured raw directory.
- A failed write does not leave a valid-looking partial JSON record.

### Exit criteria

The storage layer is reliable without requiring an LLM, network connection, or Streamlit.

## 5. Phase 2 — Capture CLI: The Archivist

### Objective

Provide one command that captures notes, links, and files and populate `raw/` with at least 10 real items.

### Tasks

1. Implement `capture.py` with mutually exclusive input modes:
   - `--text "..."`
   - `--url "https://..."`
   - `--file "path/to/file"`
2. Add optional `--title` and optional output formatting such as `--json`.
3. For notes, preserve the exact text in `content`.
4. For URLs:
   - validate the URL scheme and host format;
   - preserve the original URL in `source` and `content`;
   - defer page downloading to an optional later extractor.
5. For files:
   - preserve filename, MIME type, and file size;
   - copy the original into `raw/attachments/`;
   - extract text only when a supported extractor is configured;
   - retain the original file even when extraction fails.
6. Print the generated capture ID and raw-record path.
7. Add `--help` examples and clear validation errors.
8. Capture at least 10 real personal items, including all three supported types.
9. Record a short verification log in the README or project notes without exposing private content.

### Deliverables

- Working one-command capture pipeline.
- `raw/` populated with 10 or more real captures.
- Tests for note, URL, and file capture.
- Archivist milestone evidence.

### Verification

- Note capture creates timestamp, ID, hash, and original content.
- URL capture creates a valid `link` record.
- File capture copies the file and creates a valid `file` record.
- Re-running the command creates a new unique capture rather than overwriting one.
- At least 10 real items are present.

### Exit criteria

All Week 1 acceptance criteria from the brief are satisfied.

## 6. Phase 3 — Content normalization and PARA classification

### Objective

Transform each raw record into a readable wiki note with AI-generated category, tags, summary, and provenance.

### Tasks

1. Implement a content-extraction layer:
   - note text passes through unchanged;
   - URL text uses the URL by default and optionally extracts page content with timeouts;
   - supported text/PDF/document extractors are isolated behind adapters;
   - binary or unsupported files fall back to filename and metadata.
2. Define the `LLMClient` interface and a Groq-compatible implementation.
3. Load the API key only from environment configuration.
4. Build a classification prompt with:
   - PARA definitions;
   - strict JSON output requirements;
   - bounded tag and summary lengths;
   - explicit separation between instructions and captured content.
5. Validate model responses using the shared schema.
6. Normalize categories to exactly:
   - `projects`
   - `areas`
   - `resources`
   - `archives`
7. Implement bounded retries for transient failures and rate limits.
8. Implement a deterministic fallback when the LLM is unavailable:
   - category: `resources`;
   - title from input metadata;
   - summary from the first meaningful sentence;
   - empty tags;
   - processing status marked `degraded`.
9. Create Markdown notes in the correct PARA directory.
10. Add YAML front matter containing source ID, source path, category, tags, summary, timestamps, processing status, and model metadata.
11. Preserve the original content in the Markdown body.
12. Track status in `data/processing-state.json`.

### Deliverables

- `classify.py` and provider adapter.
- Processed Markdown wiki notes.
- Classification validation and fallback behavior.
- Processing-state tracking.

### Verification

- Every raw record can become a wiki note.
- Invalid model output does not create malformed front matter.
- A missing API key results in documented degraded behavior rather than data loss.
- Reprocessing the same record does not create duplicate wiki notes.
- Category, tags, and summary are visible in each note.

### Exit criteria

Any raw capture can be automatically or safely fallback-classified into PARA and stored in `wiki/`.

## 7. Phase 4 — Embeddings and automatic related-note links

### Objective

Use local embeddings to discover semantic relationships and write generated links between related wiki notes.

### Tasks

1. Select and configure the embedding model, defaulting to `sentence-transformers/all-MiniLM-L6-v2`.
2. Implement a local embedding adapter with:
   - model loading;
   - text truncation;
   - normalized vectors;
   - model name and dimension metadata.
3. Implement a portable embedding index under `data/`.
4. Compute embeddings for existing wiki notes and persist note IDs in the same order as vectors.
5. Implement cosine similarity with self-match exclusion.
6. Add configuration for:
   - similarity threshold, default `0.65`;
   - maximum related notes per note, default `5`;
   - minimum content length for semantic linking.
7. Compare each new or changed note with existing notes.
8. Add bidirectional generated links using stable note IDs or slugs.
9. Preserve manually authored links and distinguish them from generated links.
10. Ensure reruns do not duplicate links.
11. Add rebuild and refresh commands for embeddings and links.
12. Add unit tests for vector normalization, ranking, thresholds, top-$k$, self-matches, missing notes, and duplicate links.

### Deliverables

- `link.py` and embedding adapter.
- Persistent embedding index.
- Wiki notes containing generated related-note links.
- Rebuildable linking process.

### Verification

- The same embedding model is used for notes and future questions.
- Related notes above the threshold are linked in both directions.
- Notes below the threshold are not linked.
- Manual links remain intact after rebuilding generated links.
- At least 15 real captures are classified, embedded, and organized.

### Exit criteria

All Week 2 acceptance criteria are satisfied and the wiki can be rebuilt from raw captures.

## 8. Phase 5 — Graph data model and JSON export

### Objective

Convert the linked wiki into a versioned nodes-and-edges document that can be rendered independently of the Python pipeline.

### Tasks

1. Implement Markdown discovery under all PARA directories.
2. Parse YAML front matter with validation and useful warnings.
3. Create one node per wiki note containing:
   - stable ID;
   - label/title;
   - category;
   - tags;
   - summary;
   - bounded content preview.
4. Parse wiki links and generated related-note metadata.
5. Resolve targets by stable ID and slug.
6. Create deduplicated edges with:
   - source;
   - target;
   - relationship type;
   - similarity weight when available.
7. Handle unresolved links without crashing; emit warnings in logs.
8. Add graph schema version and generation timestamp.
9. Write `graph.json` atomically.
10. Add tests for empty wiki, malformed front matter, duplicate links, unresolved targets, self-links, and valid graph output.

### Deliverables

- `build_graph.py`.
- Versioned `graph.json` generated from real wiki data.
- Graph builder tests.

### Verification

- Every valid wiki note appears once as a node.
- Every resolvable relationship appears once as an edge.
- Graph JSON is valid and loadable independently of Streamlit.
- Content previews are truncated and sanitized for browser rendering.

### Exit criteria

The Cartographer data-model acceptance criteria are satisfied.

## 9. Phase 6 — Interactive graph interface

### Objective

Render the real knowledge graph as an interactive visual brain with hover details, drag, pan, and zoom.

### Tasks

1. Select and integrate Cytoscape.js or vis-network through a controlled Streamlit HTML component.
2. Load `graph.json` and validate its schema before rendering.
3. Map PARA categories to distinct node colors.
4. Configure a force-directed layout.
5. Add:
   - hover popups for title, summary, tags, and content preview;
   - draggable nodes;
   - pan and zoom;
   - category filtering;
   - selected-node details panel;
   - empty and malformed-graph states.
6. Escape or sanitize content inserted into HTML.
7. Cache graph data by file modification time or Streamlit cache utilities.
8. Test with a small graph, a disconnected graph, a dense graph, and an empty graph.
9. Verify behavior in a normal desktop browser and at the intended deployment size.

### Deliverables

- Graph view integrated into `app.py` or its graph component.
- Interactive rendering from real `graph.json`.
- Cartographer milestone evidence.

### Verification

- Hover reveals note content.
- Dragging, panning, and zooming work.
- Graph remains usable with at least 15 real notes.
- No raw filesystem paths or unsafe HTML are exposed.

### Exit criteria

All Week 3 acceptance criteria are satisfied.

## 10. Phase 7 — Retrieval and ask-your-brain Q&A

### Objective

Implement retrieval-augmented question answering using the user's wiki as the evidence source.

### Tasks

1. Implement `retrieve(question, top_k)` in `ask.py`.
2. Embed questions with the exact embedding model used for wiki notes.
3. Rank notes by cosine similarity.
4. Add an optional lexical boost for exact titles, tags, URLs, dates, and names.
5. Apply configurable minimum relevance and top-$k$ limits.
6. Return source IDs, titles, snippets, and scores.
7. Implement an answer prompt that:
   - supplies only retrieved notes as evidence;
   - labels each source clearly;
   - requires uncertainty when evidence is insufficient;
   - prohibits invented facts and unsupported citations.
8. Reuse the LLM provider abstraction with timeout and retry handling.
9. Return an `Answer` object containing:
   - answer text;
   - source notes;
   - retrieval scores;
   - status or error information.
10. Implement a no-evidence response instead of calling the model with an empty context.
11. Add tests for retrieval ranking, empty indexes, low-similarity questions, prompt boundaries, provider failures, and source display.
12. Test with real questions about the captured notes.

### Deliverables

- `ask.py` with retrieval and synthesis.
- Evidence-aware answer format.
- Real-question test results.

### Verification

- Relevant notes are retrieved for known questions.
- Answers cite or link to the source notes.
- Questions outside the knowledge base produce an honest limitation response.
- Retrieved note text is treated as untrusted evidence rather than instructions.

### Exit criteria

`ask()` returns answers synthesized from the user's notes through retrieval plus an LLM.

## 11. Phase 8 — Complete Streamlit application

### Objective

Combine the graph and Q&A features into one polished, safe, read-oriented application.

### Tasks

1. Build the main layout in `app.py` with:
   - application title and description;
   - graph section;
   - ask-your-brain section;
   - status and setup guidance.
2. Add a question input, submit action, retrieval-depth control, and clear answer panel.
3. Display retrieved sources with titles, summaries, and relevance values.
4. Add graph filters and selected-note details.
5. Handle missing files and configuration gracefully:
   - missing `graph.json`;
   - missing embeddings;
   - missing API key;
   - model download failure;
   - malformed wiki notes;
   - provider timeout or rate limit.
6. Keep capture and reprocessing commands outside the public app by default.
7. Cache expensive model and graph loading operations.
8. Add accessible labels, useful empty states, and responsive layout behavior.
9. Run the application locally with representative real data.

### Deliverables

- Single Streamlit application containing graph and Q&A.
- User-friendly failure and empty states.
- Local run instructions updated in `README.md`.

### Verification

- The graph and search bar appear in the same application.
- A real question returns an evidence-backed answer.
- The graph remains interactive after a search.
- App startup does not expose secrets or stack traces.

### Exit criteria

The local SecondSelf product works end to end from captured data through graph and Q&A.

## 12. Phase 9 — Deployment and final validation

### Objective

Deploy the read/query experience publicly and verify the complete system under clean-install conditions.

### Tasks

1. Prepare a deployment-safe repository:
   - remove secrets;
   - add `.env.example`;
   - decide whether personal data must be sanitized or kept in a private deployment;
   - pin compatible dependency versions.
2. Include or generate the required sanitized artifacts:
   - `wiki/`;
   - `graph.json`;
   - embedding index or a deployment-time build step.
3. Configure Streamlit Community Cloud or Hugging Face Spaces.
4. Store `GROQ_API_KEY` as a platform secret.
5. Configure `app.py` as the entry point.
6. Verify deployment logs for dependency, model, and resource issues.
7. Run smoke tests against the public URL:
   - app opens;
   - graph loads;
   - hover works;
   - drag and zoom work;
   - known question returns a source-backed answer;
   - unknown question returns an honest no-evidence response.
8. Run the complete local pipeline from a clean environment:
   `capture → classify → link → graph → ask`.
9. Record the public URL, deployment date, known limitations, and test results in `README.md`.
10. Tag the release and capture screenshots or a short demonstration if desired.

### Deliverables

- Public deployment URL.
- Clean README with setup, configuration, commands, architecture summary, and usage examples.
- End-to-end verification record.
- Oracle milestone evidence.

### Verification

- Public app is reachable without exposing credentials.
- Graph and Q&A both work from deployed artifacts.
- No private files or raw secrets are accidentally published.
- A clean checkout can reproduce the local pipeline.

### Exit criteria

All final deliverables and Week 4 acceptance criteria are satisfied.

## 13. Command-line workflow

The exact command names can evolve, but the intended workflow is:

```text
# Phase 2: capture
python capture.py --text "A note to remember"
python capture.py --url "https://example.com/article"
python capture.py --file "C:/path/to/document.pdf"

# Phase 3: classify raw captures
python classify.py

# Phase 4: build embeddings and related links
python link.py

# Phase 5: export graph data
python build_graph.py

# Phase 7+: start the application
streamlit run app.py
```

The scripts should support explicit input and output directory options or environment variables so that tests can use temporary directories without modifying real data.

## 14. Cross-phase quality gates

Every phase must meet these gates before proceeding:

1. **Correctness:** the phase acceptance tests pass.
2. **Idempotency:** running the phase twice does not create unintended duplicates.
3. **Recovery:** a single malformed item does not destroy other data.
4. **Privacy:** no secret or unauthorized personal content is logged or committed.
5. **Documentation:** the README and configuration examples describe the current behavior.
6. **Traceability:** generated artifacts can be traced back to a capture ID.
7. **Rebuildability:** derived data can be regenerated from earlier artifacts.

## 15. Test matrix

| Area | Normal case | Failure/edge case | Expected behavior |
|---|---|---|---|
| Capture | Note, URL, and file | Empty input or missing file | Clear validation error; no partial record |
| Storage | New unique record | Existing ID or interrupted write | Preserve old record; atomic recovery |
| Classification | Valid provider JSON | Timeout, invalid JSON, missing key | Retry or fallback metadata; status recorded |
| Embeddings | Multiple textual notes | Empty or incompatible model index | Skip safely or rebuild index with explanation |
| Linking | Similar notes | Self-match, duplicate, low score | Exclude or deduplicate relationship |
| Graph | Valid wiki links | Broken target or malformed front matter | Warning plus valid remaining graph |
| Retrieval | Relevant question | No relevant notes | Honest no-evidence result |
| UI | Graph and answer | Missing artifact or provider outage | Friendly setup/error state |
| Deployment | Public query | Secret or private-data risk | Block release until resolved |

## 16. Suggested implementation order within each phase

For each phase, implement in this order:

1. Define or update the data contract.
2. Implement the smallest pure functions first.
3. Add the storage or provider adapter.
4. Add the CLI or UI integration.
5. Add unit tests for normal and failure cases.
6. Run the phase-specific acceptance test using real or representative data.
7. Update README and configuration documentation.
8. Commit the phase as a logical milestone.

## 17. Final release checklist

### Archivist

- [ ] `raw/` and `wiki/` exist.
- [ ] One command captures a note, URL, and file.
- [ ] Every capture has a UTC timestamp and unique ID.
- [ ] At least 10 real captures exist.

### Librarian

- [ ] Raw captures receive category, tags, and summary.
- [ ] PARA categorization works.
- [ ] Embeddings are computed and versioned.
- [ ] Related notes are linked automatically.
- [ ] At least 15 real items are organized in `wiki/`.

### Cartographer

- [ ] `graph.json` contains valid nodes and edges.
- [ ] Graph renders interactively.
- [ ] Hover reveals note content.
- [ ] Drag, pan, and zoom work.
- [ ] Graph is built from real notes.

### Oracle

- [ ] `ask()` retrieves relevant notes and synthesizes an answer.
- [ ] Sources are visible with answers.
- [ ] Graph and search exist in one Streamlit app.
- [ ] Public deployment is reachable.
- [ ] Full pipeline has been verified end to end.

### Final deliverables

- [ ] Public GitHub repository with clean README.
- [ ] Public deployment URL or documented private deployment.
- [ ] Setup and configuration instructions.
- [ ] Test results and known limitations.
- [ ] No secrets or unauthorized private data committed.
