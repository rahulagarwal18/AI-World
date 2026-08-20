import time
import json
import logging
from typing import Dict, Any, List
from backend.groq_client import GroqEngine
from backend.tools.workspace import WorkspaceTool
from backend.tools.executor import ExecutorTool
from backend.tools.git_tool import GitTool
from backend.tools.github_api import GitHubAPITool
from backend.tools.gdrive import GDriveTool

logger = logging.getLogger("AgentLoop")

SYSTEM_PROMPT = """You are an Unrestricted Autonomous AI World Architect and Mega-Asset Engine.
You are connected to a massive 5 TB Google Drive storage vault and a high-performance execution sandbox.

YOUR MANDATE:
Do NOT create tiny, basic, or trivial scripts.
You are tasked with building EXPANSIVE, HIGH-DENSITY, COMPLEX WORLDS, PROCEDURAL UNIVERSES, AND HEAVY ASSETS!

What you should architect & build:
1. 🌌 Procedural 3D & 2D Game Worlds (Three.js 3D engines, procedural terrain generators, canvas graphics, multi-entity civilization simulators).
2. 🏛️ Complex Multi-Agent Economies & Universes (Simulated societies, trading markets, historical event logs, procedural lore books, thousands of generated entities).
3. 💾 High-Volume Synthetic Datasets & Databases (Large JSON/SQLite databases, memory graphs, procedural asset packs, texture data).
4. 🚀 Complete Web Platforms & Interactive Dashboards (Rich HTML5/JS interactive UIs, procedural audio generators, 3D visualizers).

Think BIG, think EXPONENTIAL, and generate rich, production-grade, high-density files!

Available Action Types in your JSON output:
1. {"action": "write_file", "path": "relative/file.ext", "content": "...rich expansive code/data...", "thought": "vision & architecture for this heavy asset"}
2. {"action": "execute_code", "command": "python script.py", "thought": "executing procedural generation or simulation script"}
3. {"action": "commit_and_push", "message": "commit summary", "thought": "pushing world updates to GitHub"}
4. {"action": "sync_gdrive", "file": "relative/file.ext", "thought": "syncing large world asset to 5TB Google Drive"}
5. {"action": "reflect", "thought": "architecting next expansion phase of the universe"}

Output Format:
You MUST ALWAYS respond with a SINGLE valid JSON object adhering strictly to one of the action formats above.
"""

class AgentLoop:
    def __init__(self):
        self.groq = GroqEngine()
        self.workspace = WorkspaceTool()
        self.executor = ExecutorTool()
        self.git = GitTool()
        self.github_api = GitHubAPITool()
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
            # 1. Sync to Google Drive
            gdrive_res = self.gdrive.sync_file_info(action["path"], action["content"])
            # 2. Try direct GitHub REST API commit
            gh_res = self.github_api.commit_file_direct(
                action["path"], 
                action["content"], 
                f"AI created {action['path']}: {action.get('thought', '')}"
            )
            # 3. Fallback git commit & push
            git_res = self.git.commit_and_push(f"AI created {action['path']}: {action.get('thought', '')}")
            
            res["github_api"] = gh_res
            res["gdrive"] = gdrive_res
            res["git_local"] = git_res
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
