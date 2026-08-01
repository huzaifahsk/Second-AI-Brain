"""Immutable raw capture storage utilities for Phase 1."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from config import PROJECT_ROOT, RAW_DIR
from models import CaptureRecord, CaptureType


_CAPTURE_ID_PATTERN = re.compile(r"^cap_[A-Za-z0-9TZ_\-]+$")


@dataclass
class CaptureWriteResult:
    capture_id: str
    capture_path: Path
    duplicate_of: str | None


def utc_timestamp_now() -> str:
    """Return an ISO 8601 UTC timestamp with a trailing Z."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def create_capture_id(timestamp: str | None = None) -> str:
    """Create a collision-resistant capture ID with the required prefix."""
    stamp = timestamp or utc_timestamp_now().replace(":", "").replace("-", "")
    safe_stamp = re.sub(r"[^A-Za-z0-9]", "", stamp)
    suffix = f"{random.getrandbits(32):08x}"
    return f"cap_{safe_stamp}_{suffix}"


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _resolved_raw_dir(root_dir: Path | None = None) -> Path:
    base_dir = Path(root_dir) if root_dir is not None else PROJECT_ROOT
    return base_dir / "raw" if not str(base_dir).endswith("/raw") and not str(base_dir).endswith("\\raw") else base_dir


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    _ensure_parent(path)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent), delete=False) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def validate_capture_record(payload: dict[str, Any] | CaptureRecord, *, root_dir: Path | None = None) -> CaptureRecord:
    """Validate a capture payload and ensure attachment paths are safe."""
    if isinstance(payload, CaptureRecord):
        record = payload
    else:
        parsed_time = payload.get("captured_at")
        if isinstance(parsed_time, str):
            normalized = parsed_time.replace("Z", "+00:00")
            try:
                payload = dict(payload)
                payload["captured_at"] = datetime.fromisoformat(normalized)
            except ValueError as exc:
                raise ValueError("captured_at must be a valid ISO 8601 timestamp") from exc
        record = CaptureRecord.model_validate(payload)

    if record.id and not _CAPTURE_ID_PATTERN.match(record.id):
        raise ValueError("id must match the required capture-id pattern")

    if record.type not in {CaptureType.NOTE, CaptureType.LINK, CaptureType.FILE}:
        raise ValueError("type must be note, link, or file")

    if record.attachment_path is not None:
        attachment_path = Path(record.attachment_path)
        if attachment_path.is_absolute():
            raise ValueError("attachment_path must be relative")
        if ".." in attachment_path.parts:
            raise ValueError("attachment_path must stay within the raw attachments directory")
        resolved_dir = _resolved_raw_dir(root_dir) / "attachments"
        resolved_target = (resolved_dir / attachment_path).resolve()
        try:
            resolved_target.relative_to(resolved_dir.resolve())
        except ValueError as exc:
            raise ValueError("attachment_path escapes the raw attachments directory") from exc

    return record


def write_capture_record(record: CaptureRecord, *, root_dir: Path | None = None) -> CaptureWriteResult:
    """Persist a validated capture record atomically and return write metadata."""
    validated = validate_capture_record(record, root_dir=root_dir)
    raw_dir = _resolved_raw_dir(root_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.joinpath("attachments").mkdir(parents=True, exist_ok=True)

    content_for_hash = validated.content or (validated.source or "")
    content_hash = compute_sha256(content_for_hash)
    existing_matches = [path for path in raw_dir.glob("*.json") if path.name != ".gitkeep"]
    duplicate_of: str | None = None
    for path in existing_matches:
        try:
            existing_payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        existing_hash = existing_payload.get("content_sha256")
        if existing_hash == content_hash:
            duplicate_of = existing_payload.get("id")
            break

    if validated.content_sha256 is None:
        validated.content_sha256 = content_hash

    payload = validated.model_dump(mode="json")
    payload["captured_at"] = payload["captured_at"].replace("+00:00", "Z") if isinstance(payload["captured_at"], str) else payload["captured_at"].isoformat().replace("+00:00", "Z")
    payload["type"] = validated.type.value
    payload["content_sha256"] = validated.content_sha256

    capture_path = raw_dir / f"{validated.id}.json"
    _write_json_atomic(capture_path, payload)
    return CaptureWriteResult(capture_id=validated.id, capture_path=capture_path, duplicate_of=duplicate_of)


def copy_attachment_to_raw(source_path: str | Path, *, capture_id: str, root_dir: Path | None = None) -> Path:
    """Copy a file into the raw attachments folder with a collision-safe filename."""
    source = Path(source_path)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Attachment source does not exist: {source}")

    raw_dir = _resolved_raw_dir(root_dir)
    attachments_dir = raw_dir / "attachments"
    attachments_dir.mkdir(parents=True, exist_ok=True)

    destination_name = source.name
    destination_path = attachments_dir / destination_name
    counter = 1
    while destination_path.exists():
        stem = source.stem
        suffix = source.suffix
        destination_path = attachments_dir / f"{stem}_{capture_id}{suffix if suffix else ''}"
        if not destination_path.exists():
            break
        destination_path = attachments_dir / f"{stem}_{capture_id}_{counter}{suffix if suffix else ''}"
        counter += 1
        if not destination_path.exists():
            break

    if destination_path.exists():
        raise FileExistsError(f"Attachment destination already exists: {destination_path}")

    destination_path.write_bytes(source.read_bytes())
    return destination_path
