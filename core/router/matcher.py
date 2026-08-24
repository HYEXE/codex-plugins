from pathlib import Path
import json


class CapabilityMatcher:
    def __init__(self, registry_path: str):
        self.registry = json.loads(Path(registry_path).read_text())

    def match(self, capabilities: list[str]) -> list[str]:
        result = []
        for plugin in self.registry["plugins"]:
            if set(capabilities) & set(plugin["capabilities"]):
                result.append(plugin["name"])
        return result
