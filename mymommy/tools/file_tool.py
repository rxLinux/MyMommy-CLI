from typing import Any, Dict
from mymommy.tools.base import BaseTool
from mymommy.sandbox.sandbox import Sandbox

class FileTool(BaseTool):
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "direct_pc_file_manager"

    @property
    def description(self) -> str:
        return "Acesso físico e gravação direta de dados/arquivos no HD do computador do seu filho."

    def execute(self, action: str, path: str, content: str = None) -> Any:
        if action == "read":
            return self.sandbox.read_file(path)
        elif action == "write":
            if content is None:
                content = ""
            self.sandbox.write_file(path, content)
            return f"Successfully wrote to {path}"
        elif action == "list":
            files = self.sandbox.list_files(path)
            return [str(f.relative_to(self.sandbox.base_path)) for f in files]
        else:
            raise ValueError(f"Unknown action: {action}")

    def _parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["read", "write", "list"]},
                "path": {"type": "string"},
                "content": {"type": "string", "description": "Required for 'write' action"}
            },
            "required": ["action", "path"]
        }
