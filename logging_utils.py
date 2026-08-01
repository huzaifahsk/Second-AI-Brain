"""Safe structured logging helpers for pipeline stages."""

from __future__ import annotations

import logging


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "stage"):
            record.stage = "system"
        if not hasattr(record, "capture_id"):
            record.capture_id = "-"
        if not hasattr(record, "status"):
            record.status = "-"
        return True


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("secondself")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.addFilter(ContextFilter())
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s stage=%(stage)s "
                "capture_id=%(capture_id)s status=%(status)s %(message)s"
            )
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def stage_log(logger: logging.Logger, stage: str, status: str, message: str, capture_id: str = "-") -> None:
    """Log metadata only; callers must not include secrets or private content."""
    logger.info(
        message,
        extra={"stage": stage, "capture_id": capture_id, "status": status},
    )
