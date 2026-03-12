import requests
from typing import List, Optional
from models import PullRequest, CodeChange

class GitHubClient:
    def __init__(self, token: str, repo_owner: str = None, repo_name: str = None):
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}" if repo_owner and repo_name else None
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_pull_request(self, pr_number: int) -> PullRequest:
        # Get PR details
        pr_url = f"{self.base_url}/pulls/{pr_number}"
        pr_response = requests.get(pr_url, headers=self.headers)
        pr_data = pr_response.json()

        # Get PR files (changes)
        files_url = f"{self.base_url}/pulls/{pr_number}/files"
        files_response = requests.get(files_url, headers=self.headers)
        files_data = files_response.json()

        changes = []
        for file_data in files_data:
            change = CodeChange(
                file_path=file_data["filename"],
                old_code="",  # Simplified for MVP
                new_code=file_data["patch"],
                line_start=0,
                line_end=0
            )
            changes.append(change)

        return PullRequest(
            id=pr_data["number"],
            title=pr_data["title"],
            body=pr_data["body"] or "",
            changes=changes
        )

    def post_comment(self, pr_number: int, comment: str, commit_id: str, path: str, line: int):
        comment_url = f"{self.base_url}/pulls/{pr_number}/comments"
        data = {
            "body": comment,
            "commit_id": commit_id,
            "path": path,
            "line": line
        }
        requests.post(comment_url, headers=self.headers, json=data)