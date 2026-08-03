from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_capture(*args: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["SECONDSELF_RAW_DIR"] = str(tmp_path / "raw")
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "capture.py"), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_note_capture_cli_writes_a_raw_record(tmp_path: Path) -> None:
    result = _run_capture("--text", "hello from phase 2", "--json", tmp_path=tmp_path)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["capture"]["type"] == "note"
    assert payload["capture"]["content"] == "hello from phase 2"

    raw_dir = tmp_path / "raw"
    written_files = list(raw_dir.glob("*.json"))
    assert len(written_files) == 1


def test_url_capture_cli_creates_a_link_record(tmp_path: Path) -> None:
    result = _run_capture("--url", "https://example.com/phase2", tmp_path=tmp_path)

    assert result.returncode == 0, result.stderr
    raw_dir = tmp_path / "raw"
    written_files = list(raw_dir.glob("*.json"))
    assert len(written_files) == 1

    payload = json.loads(written_files[0].read_text(encoding="utf-8"))
    assert payload["type"] == "link"
    assert payload["source"] == "https://example.com/phase2"
    assert payload["content"] == "https://example.com/phase2"


def test_file_capture_cli_copies_attachment_and_writes_record(tmp_path: Path) -> None:
    source_file = tmp_path / "sample.txt"
    source_file.write_text("sample attachment payload", encoding="utf-8")

    result = _run_capture("--file", str(source_file), tmp_path=tmp_path)

    assert result.returncode == 0, result.stderr
    raw_dir = tmp_path / "raw"
    written_files = list(raw_dir.glob("*.json"))
    assert len(written_files) == 1

    payload = json.loads(written_files[0].read_text(encoding="utf-8"))
    assert payload["type"] == "file"
    assert payload["attachment_path"].startswith("attachments/")
    assert (raw_dir / "attachments" / source_file.name).exists()
