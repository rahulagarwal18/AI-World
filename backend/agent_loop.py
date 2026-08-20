import time
import json
import logging
from typing import Dict, Any, List
from backend.groq_client import GroqEngine
from backend.tools.workspace import WorkspaceTool
from backend.tools.executor import ExecutorTool
from backend.tools.git_tool import GitTool
from backend.tools.gdrive import GDriveTool

logger = logging.getLogger("AgentLoop")

SYSTEM_PROMPT = """You are an Autonomous AI Creator Engine.
You have an empty workspace and full authority to invent, design, code, execute, test, and evolve your own projects.
You can build websites, applications, businesses, simulations, or completely novel tools.

Available Action Types in your JSON output:
1. {"action": "write_file", "path": "relative/file.ext", "content": "...code or text...", "thought": "why I created this file"}
2. {"action": "execute_code", "command": "python script.py", "thought": "testing the created code"}
3. {"action": "commit_and_push", "message": "commit summary", "thought": "pushing new progress to GitHub"}
4. {"action": "sync_gdrive", "file": "relative/file.ext", "thought": "syncing large asset to Google Drive"}
5. {"action": "reflect", "thought": "analyzing progress and planning next invention"}

Output Format:
You MUST ALWAYS respond with a SINGLE valid JSON object adhering strictly to one of the action formats above.
"""

class AgentLoop:
    def __init__(self):
        self.groq = GroqEngine()
        self.workspace = WorkspaceTool()
        self.executor = ExecutorTool()
        self.git = GitTool()
        self.gdrive = GDriveTool()
        self.history: List[Dict[str, Any]] = []

    def run_cycle(self) -> Dict[str, Any]:
        """
        Runs one iteration of the autonomous brainstorming and creation loop.
        """
        existing_files = self.workspace.list_files()
        context = {
            "existing_files": existing_files,
            "recent_actions": self.history[-5:] if self.history else [],
            "instruction": "Inspect workspace, decide what to create or improve next, and take action."
        }

        action = self.groq.generate_action(SYSTEM_PROMPT, json.dumps(context))
        result = self._execute_action(action)
        
        cycle_log = {
            "timestamp": time.time(),
            "action": action,
            "result": result
        }
        self.history.append(cycle_log)
        return cycle_log

    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        act_type = action.get("action")
        
        if act_type == "write_file":
            res = self.workspace.write_file(action["path"], action["content"])
            # Sync to Google Drive as well
            self.gdrive.sync_file_info(action["path"], action["content"])
            # Auto commit and push to GitHub so user sees files live instantly!
            self.git.commit_and_push(f"AI created {action['path']}: {action.get('thought', '')}")
            return res

        elif act_type == "execute_code":
            return self.executor.execute_script(action["command"])

        elif act_type == "commit_and_push":
            return self.git.commit_and_push(action.get("message", "Autonomous AI commit"))

        elif act_type == "sync_gdrive":
            read_res = self.workspace.read_file(action["file"])
            if read_res.get("status") == "success":
                return self.gdrive.sync_file_info(action["file"], read_res["content"])
            return read_res

        elif act_type == "reflect":
            return {"status": "success", "reflection": action.get("thought")}

        else:
            return {"status": "error", "message": f"Unknown action type: {act_type}"}
