from .agent import CommunicationAgent
class CommunicationPlanner:
    def __init__(self): self.agent=CommunicationAgent()
    def create_plan(self, request:str): return self.agent.plan(request)
    def create_draft(self, request:str): return self.agent.plan(request,True)
