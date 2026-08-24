from .matcher import CapabilityMatcher


class PluginRouter:
    def __init__(self, registry_path: str):
        self.matcher = CapabilityMatcher(registry_path)

    def route(self, capabilities: list[str]) -> list[str]:
        return self.matcher.match(capabilities)
