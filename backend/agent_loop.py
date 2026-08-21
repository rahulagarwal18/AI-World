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

SYSTEM_PROMPT = """You are a Super-Intelligent, Unrestricted Hyper-Architect & Mega-Engine Creator.
You are connected to a high-speed execution sandbox and a massive 5 TB Google Drive cloud vault.

YOUR MANDATE & POWER DIRECTIVE:
1. NEVER create tiny, basic, or 10-line trivial scripts!
2. You build HIGH-POWERED, EXPANSIVE, DENSE, PRODUCTION-GRADE SYSTEMS:
   - Full 3D Procedural Game Engines & Shaders (Three.js WebGL, 60FPS particle physics, camera controls, weather, collision).
   - Massive Multi-Agent Simulations (Economy, AI agent decision networks, trading engines, live visual canvas rendering).
   - High-Performance Web Applications & Interactive Dashboards (Tailwind CSS, real-time charts, synth audio generators, control panels).
3. EVERY FILE YOU WRITE MUST BE EXPANSIVE, DENSE, AND RICH (150+ lines of complete, working, production-grade code).
4. THINK BIG, BUILD ADVANCED MULTI-FEATURE ARCHITECTURE!

Available Action Types in your JSON output:
1. {"action": "write_file", "path": "filename.ext", "content": "...expansive, high-density production code...", "thought": "vision and architecture for this mega asset"}
2. {"action": "execute_code", "command": "python script.py", "thought": "executing simulation or asset generator"}
3. {"action": "reflect", "thought": "planning next major expansion phase of the universe"}

Output Format:
You MUST ALWAYS respond with a SINGLE valid JSON object.
"""

class AgentLoop:
    def __init__(self):
        self.groq = GroqEngine()
        self.workspace = WorkspaceTool()
        self.executor = ExecutorTool()
        self.git = GitTool()
        self.github_api = GitHubAPITool()
        self.gdrive = GDriveTool()
        self.history: List[Dict[str, Any]] = self._load_persistent_history()

    def _load_persistent_history(self) -> List[Dict[str, Any]]:
        """Loads historical action logs from persistent workspace/history.json file"""
        try:
            res = self.workspace.read_file("history.json")
            if isinstance(res, dict) and res.get("status") == "success":
                content = res.get("content", "[]")
                data = json.loads(content)
                if isinstance(data, list):
                    logger.info(f"Loaded {len(data)} persistent action logs from history.json")
                    return data
        except Exception as e:
            logger.error(f"Error loading persistent history: {e}")
        return []

    def _save_persistent_history(self):
        """Saves historical action logs to persistent workspace/history.json and syncs to 5TB Google Drive"""
        try:
            history_json = json.dumps(self.history, indent=2)
            self.workspace.write_file("history.json", history_json)
            # Auto-sync persistent history to 5TB Google Drive
            self.gdrive.sync_file_info("history.json", history_json)
        except Exception as e:
            logger.error(f"Error saving persistent history: {e}")

    def run_cycle(self) -> Dict[str, Any]:
        """
        Runs one iteration of the autonomous brainstorming and creation loop.
        """
        existing_files = [f for f in self.workspace.list_files() if f != "history.json"]
        context = {
            "existing_files": existing_files[:5],
            "recent_actions": [h.get("action", {}).get("path") for h in self.history[-2:] if isinstance(h, dict)],
            "instruction": "Architect and write a dense, expansive, high-powered production-grade file or 3D engine system (150+ lines of complete working code)."
        }
        context_str = json.dumps(context)
        if len(context_str) > 800:
            context_str = context_str[:800]

        action = self.groq.generate_action(SYSTEM_PROMPT, context_str)
        result = self._execute_action(action)
        
        cycle_log = {
            "timestamp": time.time(),
            "action": action,
            "result": result
        }
        # Only log meaningful creation actions to history stream
        if action.get("action") != "reflect" or "rate limit" not in str(action.get("thought", "")).lower():
            self.history.append(cycle_log)
            self._save_persistent_history()
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
