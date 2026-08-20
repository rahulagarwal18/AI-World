import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
from backend.config import Config

class ExecutorTool:
    def __init__(self, cwd: Path = Config.WORKSPACE_DIR):
        self.cwd = cwd

    def execute_script(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Executes a shell or Python script command inside the workspace directory.
        """
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "status": "completed",
                "returncode": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Command timed out after {timeout} seconds."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
