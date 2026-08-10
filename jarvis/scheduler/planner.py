from .agent import SchedulerAgent
class SchedulePlanner:
    def __init__(self): self.agent=SchedulerAgent()
    def create_plan(self, request:str): return self.agent.plan(request)
    def validate(self, schedule:str): return self.agent.validate(schedule)
