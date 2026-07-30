import json
from typing import Callable, Dict, Any, List

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str, description: str, parameters: dict):
        def decorator(func: Callable):
            self._tools[name] = func
            self._schemas.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            })
            return func
        return decorator

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    def execute(self, name: str, kwargs: dict) -> str:
        if name not in self._tools:
            return f"Error: Tool '{name}' not found in registry."
        try:
            result = self._tools[name](**kwargs)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"

registry = ToolRegistry()
