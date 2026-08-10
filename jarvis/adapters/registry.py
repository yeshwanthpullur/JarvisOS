from .agent import default_adapter_manifests
class AdapterManifestRegistry:
    def __init__(self): self.manifests=default_adapter_manifests()
    def list_adapters(self): return self.manifests
    def get_adapter(self, adapter_id): return next((x for x in self.manifests if x.adapter_id==adapter_id),None)
