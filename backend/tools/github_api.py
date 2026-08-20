import os
import base64
import logging
import httpx
from backend.config import Config

logger = logging.getLogger("GitHubAPI")

class GitHubAPITool:
    def __init__(self, username: str = Config.GITHUB_USERNAME, repo: str = "AI-World"):
        self.username = username
        self.repo = repo

    def commit_file_direct(self, rel_path: str, content: str, commit_msg: str) -> dict:
        """
        Commits a file directly to the GitHub repository using the GitHub REST API.
        """
        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token:
            logger.warning("GITHUB_TOKEN not set in environment variables.")
            return {"status": "skipped", "reason": "No GITHUB_TOKEN configured."}

        target_path = f"workspace/{rel_path}".replace("//", "/")
        url = f"https://api.github.com/repos/{self.username}/{self.repo}/contents/{target_path}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        # Check if file exists to get SHA for update
        sha = None
        try:
            get_res = httpx.get(url, headers=headers, timeout=10)
            if get_res.status_code == 200:
                sha = get_res.json().get("sha")
        except Exception as e:
            logger.warning(f"Error checking file SHA on GitHub: {e}")

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        payload = {
            "message": commit_msg,
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha

        try:
            put_res = httpx.put(url, headers=headers, json=payload, timeout=15)
            if put_res.status_code in [200, 201]:
                logger.info(f"Successfully committed {target_path} to GitHub!")
                return {"status": "success", "file": target_path, "url": put_res.json().get("content", {}).get("html_url")}
            else:
                # Try fallback header 'token <token>'
                headers["Authorization"] = f"token {token}"
                put_res2 = httpx.put(url, headers=headers, json=payload, timeout=15)
                if put_res2.status_code in [200, 201]:
                    logger.info(f"Successfully committed {target_path} to GitHub!")
                    return {"status": "success", "file": target_path, "url": put_res2.json().get("content", {}).get("html_url")}
                
                logger.error(f"GitHub API commit failed: {put_res2.status_code} - {put_res2.text}")
                return {"status": "error", "code": put_res2.status_code, "response": put_res2.text}
        except Exception as e:
            logger.error(f"Failed GitHub API request: {e}")
            return {"status": "error", "message": str(e)}
