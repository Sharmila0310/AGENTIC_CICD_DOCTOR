import os
from github import Github, Auth

class GitHubPRService:
    def __init__(self, token: str = None):
        self.gh = Github(auth=Auth.Token(token or os.getenv("GITHUB_TOKEN")))

    def create_pr(self, repo_name: str, branch: str, changes: list, thoughts: str) -> str:
        repo = self.gh.get_repo(repo_name)
        ref_sha = repo.get_branch(branch).commit.sha
        fix_branch = f"fix/cicd-{ref_sha[:7]}"
        
        repo.create_git_ref(ref=f"refs/heads/{fix_branch}", sha=ref_sha)
        for c in changes:
            path, content = c["file_path"], c["replacement_code"]
            try:
                sha = repo.get_contents(path, ref=fix_branch).sha
                repo.update_file(path, "fix(ci): repair", content, sha, branch=fix_branch)
            except Exception:
                repo.create_file(path, "fix(ci): repair", content, branch=fix_branch)

        pr = repo.create_pull(
            title=f"🤖 [CI Doctor] Fix for {ref_sha[:7]}",
            body=f"### Agent Diagnosis\n{thoughts}",
            head=fix_branch, base=branch
        )
        return pr.html_url