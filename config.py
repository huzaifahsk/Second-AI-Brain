"""Shared project configuration and path resolution for SecondSelf."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


def _path_setting(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default)).expanduser()
    return value if value.is_absolute() else PROJECT_ROOT / value


RAW_DIR = _path_setting("SECONDSELF_RAW_DIR", "raw")
WIKI_DIR = _path_setting("SECONDSELF_WIKI_DIR", "wiki")
DATA_DIR = _path_setting("SECONDSELF_DATA_DIR", "data")
STATIC_DIR = _path_setting("SECONDSELF_STATIC_DIR", "static")
GRAPH_PATH = _path_setting("SECONDSELF_GRAPH_PATH", "data/graph.json")

LLM_MODEL = os.getenv("SECONDSELF_LLM_MODEL", "llama-3.1-8b-instant")
EMBEDDING_MODEL = os.getenv(
    "SECONDSELF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
SIMILARITY_THRESHOLD = float(os.getenv("SECONDSELF_SIMILARITY_THRESHOLD", "0.65"))
TOP_K = int(os.getenv("SECONDSELF_TOP_K", "5"))
MAX_RELATED_NOTES = int(os.getenv("SECONDSELF_MAX_RELATED_NOTES", "5"))
MAX_CONTENT_CHARS = int(os.getenv("SECONDSELF_MAX_CONTENT_CHARS", "12000"))


def ensure_directories() -> None:
    """Create runtime directories required by the pipeline."""
    for path in (
        RAW_DIR,
        RAW_DIR / "attachments",
        WIKI_DIR / "projects",
        WIKI_DIR / "areas",
        WIKI_DIR / "resources",
        WIKI_DIR / "archives",
        DATA_DIR,
        STATIC_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
