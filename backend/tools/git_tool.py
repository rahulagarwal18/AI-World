import subprocess
from pathlib import Path
from typing import Dict, Any
from backend.config import Config

class GitTool:
    def __init__(self, repo_dir: Path = Config.WORKSPACE_DIR, repo_url: str = Config.GITHUB_REPO_URL):
        self.repo_dir = repo_dir
        self.repo_url = repo_url

    def commit_and_push(self, commit_message: str) -> Dict[str, Any]:
        """
        Initializes git (if needed), adds all files, commits, and pushes to remote.
        """
        try:
            # Ensure git initialized
            subprocess.run("git init", shell=True, cwd=self.repo_dir, capture_output=True)
            subprocess.run(f"git remote add origin {self.repo_url}", shell=True, cwd=self.repo_dir, capture_output=True)
            
            # Add & commit
            subprocess.run("git add .", shell=True, cwd=self.repo_dir, capture_output=True)
            res_commit = subprocess.run(
                f'git commit -m "{commit_message}"',
                shell=True,
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            # Push
            res_push = subprocess.run(
                "git push -u origin main",
                shell=True,
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            
            return {
                "status": "success",
                "commit_output": res_commit.stdout,
                "push_output": res_push.stdout or res_push.stderr,
                "repo_url": self.repo_url
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
