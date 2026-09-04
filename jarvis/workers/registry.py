"""Canonical registry for governed external worker adapters."""

from __future__ import annotations

import json

from .adapters import MetadataWorkerAdapter, OpenCodeAdapter, build_default_adapters
from .models import WorkerRecord, WorkerStatus


class WorkerRegistry:
    def __init__(self, adapters: tuple[MetadataWorkerAdapter, ...] = (), max_workers: int = 32) -> None:
        self.max_workers = max(1, min(max_workers, 64))
        self._adapters: dict[str, MetadataWorkerAdapter] = {}
        self._records: dict[str, WorkerRecord] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: MetadataWorkerAdapter) -> None:
        if adapter.worker_id in self._adapters:
            raise ValueError(f"duplicate_worker:{adapter.worker_id}")
        if len(self._adapters) >= self.max_workers:
            raise ValueError("worker_registry_limit_exceeded")
        self._adapters[adapter.worker_id] = adapter

    def adapter(self, worker_id: str) -> MetadataWorkerAdapter | None:
        return self._adapters.get(worker_id)

    def refresh(self, *, health: bool = False) -> tuple[WorkerRecord, ...]:
        self._records = {
            worker_id: (adapter.health() if health else adapter.detect())
            for worker_id, adapter in self._adapters.items()
        }
        return self.list()

    def list(self) -> tuple[WorkerRecord, ...]:
        for worker_id, adapter in self._adapters.items():
            if worker_id not in self._records:
                self._records[worker_id] = adapter.detect()
        return tuple(self._records[key] for key in sorted(self._records))

    def get(self, worker_id: str) -> WorkerRecord | None:
        if worker_id not in self._records and worker_id in self._adapters:
            self._records[worker_id] = self._adapters[worker_id].detect()
        return self._records.get(worker_id)

    def available(self) -> tuple[WorkerRecord, ...]:
        return tuple(item for item in self.list() if item.status in {WorkerStatus.READY, WorkerStatus.DEGRADED})

    def validate(self) -> tuple[str, ...]:
        errors = []
        if len(self._adapters) > self.max_workers:
            errors.append("worker_registry_limit_exceeded")
        for item in self.list():
            if item.authority != "external_worker_only":
                errors.append(f"invalid_authority:{item.worker_id}")
            if item.status is WorkerStatus.READY and not item.execution_enabled:
                errors.append(f"ready_but_disabled:{item.worker_id}")
        return tuple(errors[:32])

    def summary(self) -> dict[str, int | bool]:
        records = self.list()
        return {
            "registered": len(records),
            "detected": sum(item.status in {WorkerStatus.READY, WorkerStatus.DEGRADED} for item in records),
            "unavailable": sum(item.status is WorkerStatus.UNAVAILABLE for item in records),
            "execution_enabled": sum(item.execution_enabled for item in records),
            "valid": not self.validate(),
        }

    def inventory_json(self) -> str:
        payload = {
            "schema_version": 1,
            "authority": "metadata_and_plan_only",
            "workers": [
                {
                    "worker_id": item.worker_id,
                    "display_name": item.display_name,
                    "adapter_type": item.adapter_type,
                    "status": item.status.value,
                    "version": item.detected_version,
                    "detected": item.detected,
                    "configured": item.configured,
                    "authenticated": item.authenticated,
                    "healthy": item.healthy,
                    "source": item.discovery_source,
                    "workspace_modes": [mode.value for mode in item.workspace_modes],
                    "capabilities": {
                        "planning": item.capabilities.planning,
                        "repository_read": item.capabilities.repository_read,
                        "repository_write": item.capabilities.repository_write,
                        "streaming": item.capabilities.streaming,
                        "sessions": item.capabilities.sessions,
                        "resume": item.capabilities.resume,
                        "tool_use": item.capabilities.tool_use,
                        "review": item.capabilities.independent_review,
                        "research": item.capabilities.research,
                        "local_models": item.capabilities.local_models,
                        "cloud_models": item.capabilities.cloud_models,
                        "supported_task_types": item.capabilities.supported_task_types,
                    },
                    "execution_enabled": item.execution_enabled,
                    "approval_required": item.approval_required,
                    "workspace_policy": item.workspace_policy,
                    "permission_policy": item.permission_policy,
                    "cost_class": item.cost_class,
                    "availability": item.availability,
                    "last_health_check": item.last_health_check,
                    "health_reason": item.health_reason,
                }
                for item in self.list()
            ],
        }
        return json.dumps(payload, sort_keys=True)


def build_default_worker_registry(max_workers: int = 32) -> WorkerRegistry:
    return WorkerRegistry(build_default_adapters(), max_workers=max_workers)


def opencode_adapter(registry: WorkerRegistry) -> OpenCodeAdapter | None:
    adapter = registry.adapter("opencode")
    return adapter if isinstance(adapter, OpenCodeAdapter) else None
