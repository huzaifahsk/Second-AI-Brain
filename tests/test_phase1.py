from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from models import CaptureRecord, CaptureType
from storage import (
    compute_sha256,
    copy_attachment_to_raw,
    create_capture_id,
    utc_timestamp_now,
    validate_capture_record,
    write_capture_record,
)


def test_timestamp_and_id_format_are_stable() -> None:
    timestamp = utc_timestamp_now()
    assert timestamp.endswith("Z")
    capture_id = create_capture_id(timestamp)
    assert capture_id.startswith("cap_")
    assert len(capture_id.split("_")) >= 3


def test_sha256_is_stable_for_content() -> None:
    content = "hello secondself"
    assert compute_sha256(content) == compute_sha256(content)


def test_write_capture_record_persists_and_returns_path(tmp_path: Path) -> None:
    record = CaptureRecord(
        id=create_capture_id(),
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.NOTE,
        title="A note",
        content="hello",
    )

    result = write_capture_record(record, root_dir=tmp_path)

    assert result.capture_path.exists()
    saved = json.loads(result.capture_path.read_text(encoding="utf-8"))
    assert saved["id"] == record.id
    assert saved["content"] == "hello"


def test_duplicate_content_is_reported_without_overwriting(tmp_path: Path) -> None:
    record_a = CaptureRecord(
        id=create_capture_id(),
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.NOTE,
        title="First",
        content="same content",
    )
    record_b = CaptureRecord(
        id=create_capture_id(),
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.NOTE,
        title="Second",
        content="same content",
    )

    first = write_capture_record(record_a, root_dir=tmp_path)
    second = write_capture_record(record_b, root_dir=tmp_path)

    assert second.duplicate_of == first.capture_id
    assert second.capture_path.exists()
    assert first.capture_path.exists()


def test_copy_attachment_stays_inside_raw_attachments(tmp_path: Path) -> None:
    source_path = tmp_path / "source.txt"
    source_path.write_text("hello attachment", encoding="utf-8")

    destination = copy_attachment_to_raw(source_path, capture_id="cap_test", root_dir=tmp_path)

    assert destination.exists()
    assert destination.is_relative_to(tmp_path / "raw" / "attachments")
    assert destination.read_text(encoding="utf-8") == "hello attachment"


def test_path_traversal_attachment_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        validate_capture_record(
            {
                "id": "cap_test",
                "captured_at": "2026-08-02T00:00:00Z",
                "type": "note",
                "title": "bad",
                "content": "body",
                "attachment_path": "../outside.txt",
            },
            root_dir=tmp_path,
        )
