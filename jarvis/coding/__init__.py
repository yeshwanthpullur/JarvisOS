"""Safe, local-first Coding Agent foundation."""

from .agent import CodingAgent
from .cli import render_coding_command
from .diff import DiffReviewer
from .models import CodingIntent, CodingPlan, CodingResult, CodingRiskLevel, CodingStatus, CodingTask, DiffReview, RepoInspection
from .planner import CodingPlanner, classify_coding_intent
from .repo import RepoInspector, safe_repo_name
from .safety import CodingSafetyDecision, evaluate_coding_safety, redact_secret_shaped
from .storage import CodingHistoryRecord, CodingHistoryStore

__all__ = [
    "CodingAgent", "CodingHistoryRecord", "CodingHistoryStore", "CodingIntent", "CodingPlan",
    "CodingPlanner", "CodingResult", "CodingRiskLevel", "CodingSafetyDecision", "CodingStatus",
    "CodingTask", "DiffReview", "DiffReviewer", "RepoInspection", "RepoInspector",
    "classify_coding_intent", "evaluate_coding_safety", "redact_secret_shaped", "render_coding_command",
    "safe_repo_name",
]
