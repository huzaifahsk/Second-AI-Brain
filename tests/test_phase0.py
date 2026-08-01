from datetime import datetime, timezone

from config import PROJECT_ROOT, ensure_directories
from models import CaptureRecord, CaptureType, PARACategory


def test_paths_are_resolved_from_project_root() -> None:
    assert PROJECT_ROOT.name == "Your Second AI Brain"


def test_runtime_directories_can_be_created() -> None:
    ensure_directories()


def test_capture_contract_accepts_note() -> None:
    record = CaptureRecord(
        id="cap_20260801T143022Z_test",
        captured_at=datetime.now(timezone.utc),
        type=CaptureType.NOTE,
        content="A note",
    )
    assert record.type == CaptureType.NOTE


def test_classification_contract_uses_para_values() -> None:
    from models import Classification

    result = Classification(
        category=PARACategory.RESOURCES,
        summary="A resource summary.",
    )
    assert result.category == PARACategory.RESOURCES
