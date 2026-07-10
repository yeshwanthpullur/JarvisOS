"""Project management layer for task intelligence."""

from __future__ import annotations

import logging

from task_intelligence.models import ProjectRecord


class ProjectManager:
    """Create and track projects for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._projects: dict[str, ProjectRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("project_manager_initialized")

    def create_project(self, name: str, description: str = "") -> ProjectRecord:
        self._ensure_initialized()
        project = ProjectRecord(name=name, description=description)
        self._projects[project.project_id] = project
        self._logger.info("project_created project_id=%s", project.project_id)
        return project

    def list_projects(self) -> tuple[ProjectRecord, ...]:
        self._ensure_initialized()
        return tuple(self._projects.values())

    def statistics(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"projects": len(self._projects), "status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ProjectManager must be initialized before use.")
