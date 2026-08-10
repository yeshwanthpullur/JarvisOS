from pathlib import Path
from .agent import DocumentAgent
class DocumentPlanner:
    def __init__(self, root: Path | None = None): self.agent=DocumentAgent(root or Path.cwd())
    def create_plan(self, request: str): return self.agent.plan(request)
