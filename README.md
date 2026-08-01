# SecondSelf — Your Personal AI Second Brain

SecondSelf is a local-first knowledge system for capturing notes, links, and files, organizing them with PARA, discovering related knowledge, visualizing a graph, and asking evidence-grounded questions.

## Phase 0 status

The project foundation is in place:

- runtime directories for raw captures, wiki notes, indexes, static assets, and tests;
- environment-based configuration resolved relative to the repository root;
- shared Pydantic contracts in `models.py`;
- safe stage-aware logging in `logging_utils.py`;
- dependency and secret-handling conventions.

The capture and processing commands will be added in later phases.

## Setup on Windows

1. Create and activate a virtual environment:
   `C:/Users/Huzaifah Shaikh/AppData/Local/Programs/Python/Python313/python.exe -m venv .venv`
2. Install dependencies:
   `.venv\\Scripts\\python.exe -m pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set provider secrets only when needed.
4. Verify the foundation:
   `.venv\\Scripts\\python.exe -c "from config import ensure_directories; from models import CaptureRecord; ensure_directories(); print('SecondSelf Phase 0 OK')"`

The repository path may contain spaces; configuration uses absolute paths derived from `config.py`, so commands do not depend on the current working directory.

## Planned workflow

```text
python capture.py --text "A note to remember"
python capture.py --url "https://example.com/article"
python capture.py --file "C:/path/to/document.pdf"
python classify.py
python link.py
python build_graph.py
streamlit run app.py
```

## Privacy and generated data

Never commit `.env`, API keys, private attachments, raw captures, or generated private indexes. Raw captures are intended to be immutable; later pipeline stages produce rebuildable derived artifacts. Public deployments should contain only sanitized data and should expose read/query behavior rather than write-capable capture commands.

See [docs/architecture.md](docs/architecture.md), [docs/implementation-plan.md](docs/implementation-plan.md), and [docs/edge-case.md](docs/edge-case.md) for the design and delivery plan.
