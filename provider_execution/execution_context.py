"""Runtime context for provider execution orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProviderExecutionContext:
    """References required by the execution framework.

    The context intentionally stores references as interfaces or opaque objects
    so the execution framework does not depend on concrete subsystems.
    """

    provider_router: Any | None = None
    provider_manager: Any | None = None
    settings: Any | None = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("provider_execution"))
    metadata: dict[str, Any] = field(default_factory=dict)
