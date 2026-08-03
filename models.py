"""Pydantic contracts shared by SecondSelf pipeline stages."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaptureType(StrEnum):
    NOTE = "note"
    LINK = "link"
    FILE = "file"


class PARACategory(StrEnum):
    PROJECTS = "projects"
    AREAS = "areas"
    RESOURCES = "resources"
    ARCHIVES = "archives"


class CaptureRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^cap_[A-Za-z0-9TZ_\-]+$")
    captured_at: datetime
    type: CaptureType
    title: str = "Untitled capture"
    content: str = ""
    source: str | None = None
    attachment_path: str | None = None
    content_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    schema_version: int = Field(default=1, ge=1)
    mime_type: str | None = None
    file_size: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_content_or_source(self) -> "CaptureRecord":
        if not self.content.strip() and not (self.source and self.source.strip()):
            raise ValueError("content or source must be non-empty")
        return self


class Classification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: PARACategory
    tags: list[str] = Field(default_factory=list, max_length=12)
    summary: str = Field(min_length=1, max_length=500)
    title: str | None = Field(default=None, max_length=200)
    status: str = "complete"


class WikiNote(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_capture: str
    category: PARACategory
    tags: list[str] = Field(default_factory=list)
    summary: str
    created_at: datetime
    processed_at: datetime
    processing_status: str = "complete"
    embedding_model: str | None = None
    model_metadata: dict[str, Any] = Field(default_factory=dict)


class RelatedNote(BaseModel):
    note_id: str
    similarity: float = Field(ge=-1.0, le=1.0)
    relationship: str = "generated"


class RetrievedNote(BaseModel):
    note_id: str
    title: str
    snippet: str
    score: float
    source_path: str | None = None


class Answer(BaseModel):
    answer: str
    sources: list[RetrievedNote] = Field(default_factory=list)
    status: str = "complete"
    error: str | None = None
