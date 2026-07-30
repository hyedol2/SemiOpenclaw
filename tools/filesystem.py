import os
from tools.registry import registry

@registry.register(
    name="list_directory",
    description="List files and directories in a given path.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (defaults to current directory)", "default": "."}
        },
        "required": []
    }
)
def list_directory(path: str = ".") -> str:
    try:
        items = os.listdir(path)
        return f"Contents of '{path}':\n" + "\n".join(items)
    except Exception as e:
        return f"Failed to list directory: {str(e)}"
