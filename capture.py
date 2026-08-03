"""CLI entry point for capturing notes, links, and files into the raw repository."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from config import PROJECT_ROOT, RAW_DIR
from logging_utils import configure_logging, stage_log
from models import CaptureRecord, CaptureType
from storage import copy_attachment_to_raw, create_capture_id, write_capture_record


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture a note, URL, or file into the immutable raw repository.",
        epilog="Examples:\n  python capture.py --text \"A note to remember\"\n  python capture.py --url https://example.com\n  python capture.py --file ./notes.pdf",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Capture a freeform note")
    input_group.add_argument("--url", help="Capture a URL")
    input_group.add_argument("--file", help="Capture a file from disk")
    parser.add_argument("--title", help="Optional title for the capture")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--root-dir",
        default=str(RAW_DIR),
        help="Base output directory for raw captures (defaults to the configured raw directory)",
    )
    return parser


def _resolve_output_root(root_dir: str | None) -> Path:
    if root_dir:
        return Path(root_dir).expanduser().resolve()
    return RAW_DIR.resolve()


def _validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must use http or https and include a host")
    return value


def _capture_note(text: str, title: str | None, output_root: Path) -> CaptureRecord:
    return CaptureRecord(
        id=create_capture_id(),
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.NOTE,
        title=title or "Captured note",
        content=text,
        source=None,
    )


def _capture_url(url: str, title: str | None, output_root: Path) -> CaptureRecord:
    normalized = _validate_url(url)
    return CaptureRecord(
        id=create_capture_id(),
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.LINK,
        title=title or f"Link: {urlparse(normalized).netloc}",
        content=normalized,
        source=normalized,
    )


def _capture_file(file_path: str, title: str | None, output_root: Path) -> CaptureRecord:
    source = Path(file_path).expanduser()
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"File does not exist: {source}")

    mime_type, _ = mimetypes.guess_type(str(source))
    file_size = source.stat().st_size
    capture_id = create_capture_id()
    destination = copy_attachment_to_raw(source, capture_id=capture_id, root_dir=output_root)
    attachment_path = destination.relative_to(output_root).as_posix()

    return CaptureRecord(
        id=capture_id,
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.FILE,
        title=title or source.name,
        content=f"{source.name} ({file_size} bytes)",
        source=str(source),
        attachment_path=attachment_path,
        mime_type=mime_type or "application/octet-stream",
        file_size=file_size,
    )


def _serialize_capture(record: CaptureRecord, output_root: Path, result: Any) -> dict[str, Any]:
    return {
        "capture": {
            "id": record.id,
            "type": record.type.value,
            "title": record.title,
            "content": record.content,
            "source": record.source,
            "attachment_path": record.attachment_path,
            "capture_path": str(result.capture_path.relative_to(output_root)) if result.capture_path.is_relative_to(output_root) else str(result.capture_path),
            "duplicate_of": result.duplicate_of,
        }
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logger = configure_logging()

    output_root = _resolve_output_root(args.root_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        if args.text is not None:
            stage_log(logger, "capture", "start", "capturing note")
            record = _capture_note(args.text, args.title, output_root)
        elif args.url is not None:
            stage_log(logger, "capture", "start", "capturing URL")
            record = _capture_url(args.url, args.title, output_root)
        else:
            stage_log(logger, "capture", "start", "capturing file")
            record = _capture_file(args.file, args.title, output_root)

        result = write_capture_record(record, root_dir=output_root)
        stage_log(logger, "capture", "complete", "capture written", capture_id=record.id)
        payload = _serialize_capture(record, output_root, result)
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Captured {record.type.value} {record.id}")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
