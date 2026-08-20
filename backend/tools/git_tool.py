import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any
from backend.config import Config

logger = logging.getLogger("GitTool")

class GitTool:
    def __init__(self, repo_dir: Path = Config.WORKSPACE_DIR, repo_url: str = Config.GITHUB_REPO_URL):
        self.repo_dir = repo_dir
        self.raw_repo_url = repo_url

    def _get_authed_url(self) -> str:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if token and "github.com" in self.raw_repo_url and "@" not in self.raw_repo_url:
            return self.raw_repo_url.replace("https://", f"https://{token}@")
        return self.raw_repo_url

    def commit_and_push(self, commit_message: str) -> Dict[str, Any]:
        """
        Initializes git (if needed), renames branch to main, adds files, commits, and pushes to remote.
        """
        try:
            authed_url = self._get_authed_url()
            subprocess.run("git init", shell=True, cwd=self.repo_dir, capture_output=True)
            subprocess.run(f"git remote set-url origin {authed_url} || git remote add origin {authed_url}", shell=True, cwd=self.repo_dir, capture_output=True)
            
            subprocess.run("git config user.name 'AI Creator Engine'", shell=True, cwd=self.repo_dir, capture_output=True)
            subprocess.run("git config user.email 'ai@creation.engine'", shell=True, cwd=self.repo_dir, capture_output=True)
            
            # Ensure branch name is main
            subprocess.run("git branch -M main", shell=True, cwd=self.repo_dir, capture_output=True)

            subprocess.run("git add .", shell=True, cwd=self.repo_dir, capture_output=True)
            res_commit = subprocess.run(
                f'git commit -m "{commit_message}"',
                shell=True,
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            res_push = subprocess.run(
                "git push -u origin main --force",
                shell=True,
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            return {
                "status": "success",
                "commit_output": res_commit.stdout,
                "push_output": res_push.stdout or res_push.stderr
            }
        except Exception as e:
            logger.error(f"Git push failed: {e}")
            return {"status": "error", "message": str(e)}
