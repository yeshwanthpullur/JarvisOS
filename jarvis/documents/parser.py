from pathlib import Path
from .agent import DocumentAgent
class SafeDocumentParser:
    def __init__(self, root: Path | None = None): self.agent=DocumentAgent(root or Path.cwd())
    def inspect(self, ref: str): return self.agent.inspect(ref)
    def extract(self, ref: str): return self.agent.extract(ref)
