"""Documentation reader interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class DocumentKind(StrEnum):
    """Document formats future readers may support."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"
    DOCX = "docx"
    TXT = "txt"


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """Reference to a local or remote document."""

    location: Path | str
    kind: DocumentKind
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodeBlock:
    """Code extracted from documentation."""

    language: str
    content: str
    source_location: str | None = None


@dataclass(frozen=True, slots=True)
class CommandBlock:
    """Executable command extracted from documentation."""

    command: str
    shell: str | None = None
    source_location: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentContent:
    """Normalized document content."""

    reference: DocumentReference
    text: str
    code_blocks: tuple[CodeBlock, ...] = ()
    commands: tuple[CommandBlock, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Plan generated from documentation without executing it."""

    summary: str
    commands: tuple[CommandBlock, ...]
    required_files: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()


class DocumentationReader(ABC):
    """Interface for reading docs and extracting implementation guidance."""

    @abstractmethod
    def read(self, reference: DocumentReference) -> DocumentContent:
        """Read and normalize a document."""

    @abstractmethod
    def extract_code_blocks(self, content: DocumentContent) -> tuple[CodeBlock, ...]:
        """Extract code blocks from normalized content."""

    @abstractmethod
    def extract_commands(self, content: DocumentContent) -> tuple[CommandBlock, ...]:
        """Extract shell commands from normalized content."""

    @abstractmethod
    def create_execution_plan(self, content: DocumentContent) -> ExecutionPlan:
        """Create a non-executing plan from documentation."""

