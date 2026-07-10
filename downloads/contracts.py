"""Download manager interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class DownloadKind(StrEnum):
    """Supported future download categories."""

    FILE = "file"
    GITHUB_REPOSITORY = "github_repository"
    DATASET = "dataset"
    DOCUMENTATION = "documentation"


@dataclass(frozen=True, slots=True)
class DownloadIntegrity:
    """Integrity requirements for a future download."""

    checksum: str | None = None
    algorithm: str | None = None
    signature_url: str | None = None


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    """Provider-neutral download request."""

    source: str
    destination: Path
    kind: DownloadKind
    integrity: DownloadIntegrity | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DownloadProgress:
    """Download progress event."""

    request_id: str
    bytes_received: int
    total_bytes: int | None
    message: str = ""


@dataclass(frozen=True, slots=True)
class DownloadResult:
    """Final download result."""

    request_id: str
    destination: Path
    verified: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)


class DownloadManager(ABC):
    """Interface for future queued and verified downloads."""

    @abstractmethod
    def enqueue(self, request: DownloadRequest) -> str:
        """Add a download to the queue and return its request ID."""

    @abstractmethod
    def progress(self, request_id: str) -> DownloadProgress | None:
        """Return current progress for a queued download."""

    @abstractmethod
    def cancel(self, request_id: str) -> None:
        """Cancel a queued or active download."""

    @abstractmethod
    def organize(self, request_id: str, category: str) -> Path:
        """Move or classify a completed download without changing its contents."""

    @abstractmethod
    def verify_integrity(self, request_id: str) -> bool:
        """Verify a completed download against its integrity contract."""

    @abstractmethod
    def result(self, request_id: str) -> DownloadResult | None:
        """Return the completed result, if available."""
