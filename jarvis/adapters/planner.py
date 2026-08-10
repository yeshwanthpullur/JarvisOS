from .agent import AdapterAgent
class AdapterPlanner:
    def __init__(self): self.agent=AdapterAgent()
    def create_plan(self, request:str): return self.agent.plan(request)
