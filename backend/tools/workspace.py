from pathlib import Path
from typing import Dict, Any, List
from backend.config import Config

class WorkspaceTool:
    def __init__(self, root: Path = Config.WORKSPACE_DIR):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._sync_from_git()

    def _sync_from_git(self):
        try:
            import subprocess
            subprocess.run("git pull origin main", shell=True, cwd=self.root.parent, capture_output=True)
        except Exception:
            pass

    def _resolve_path(self, rel_path: str) -> Path:
        target = (self.root / rel_path).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError(f"Access denied: path {rel_path} outside workspace.")
        return target

    def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        target = self._resolve_path(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return {"status": "success", "file": rel_path, "bytes": len(content)}

    def read_file(self, rel_path: str) -> Dict[str, Any]:
        target = self._resolve_path(rel_path)
        if not target.exists():
            return {"status": "error", "message": f"File {rel_path} does not exist."}
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        return {"status": "success", "file": rel_path, "content": content}

    def list_files(self) -> List[str]:
        files = []
        for p in self.root.rglob("*"):
            if p.is_file() and ".git" not in p.parts:
                files.append(str(p.relative_to(self.root)).replace("\\", "/"))
        return files
