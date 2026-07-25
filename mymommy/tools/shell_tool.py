import subprocess
import os
from typing import Any, Dict
from mymommy.tools.base import BaseTool
from mymommy.sandbox.sandbox import Sandbox

class ShellTool(BaseTool):
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    @property
    def name(self) -> str:
        return "direct_pc_terminal_executor"

    @property
    def description(self) -> str:
        return "Executa instruções e comandos de terminal diretamente no processador e sistema operacional do computador do seu filho."

    def execute(self, command: str) -> Any:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.sandbox.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"}
            },
            "required": ["command"]
        }
