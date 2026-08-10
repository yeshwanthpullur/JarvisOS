from .agent import default_communication_providers
class CommunicationProviderRegistry:
    def __init__(self): self.providers=default_communication_providers()
    def list_providers(self): return self.providers
    def get_provider(self, provider_id): return next((x for x in self.providers if x.provider_id==provider_id),None)
