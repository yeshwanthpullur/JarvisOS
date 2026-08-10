from .agent import BrowserAgent
class BrowserPlanner:
    def __init__(self): self.agent=BrowserAgent()
    def create_plan(self, request:str): return self.agent.plan(request)
