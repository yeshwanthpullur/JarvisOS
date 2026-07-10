"""Installer framework interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class InstallationStepStatus(StrEnum):
    """Lifecycle state for planned installation steps."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class InstallerSource:
    """Source material used to plan an installation."""

    root: Path
    readme: Path | None = None
    installation_guide: Path | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class InstallationStep:
    """Single planned installation action."""

    name: str
    description: str
    command: str | None = None
    status: InstallationStepStatus = InstallationStepStatus.PENDING


@dataclass(frozen=True, slots=True)
class InstallationPlan:
    """Installation plan generated from source documentation."""

    source: InstallerSource
    dependencies: tuple[str, ...]
    steps: tuple[InstallationStep, ...]
    rollback_steps: tuple[InstallationStep, ...] = ()


@dataclass(frozen=True, slots=True)
class InstallationReport:
    """Result report for a future installation run."""

    plan: InstallationPlan
    successful: bool
    messages: tuple[str, ...] = ()
    artifacts: tuple[Path, ...] = ()


class Installer(ABC):
    """Interface for planning, running, verifying, and rolling back installs."""

    @abstractmethod
    def inspect(self, source: InstallerSource) -> InstallationPlan:
        """Read source docs and produce an installation plan."""

    @abstractmethod
    def run(self, plan: InstallationPlan) -> InstallationReport:
        """Run a previously approved installation plan."""

    @abstractmethod
    def verify(self, plan: InstallationPlan) -> bool:
        """Verify that installation succeeded."""

    @abstractmethod
    def rollback(self, plan: InstallationPlan) -> InstallationReport:
        """Rollback a failed or unwanted installation."""

