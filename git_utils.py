import os
from github import Github, GithubException

def create_github_pr(repo_name: str, file_path: str, fixed_code: str, commit_message: str):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("[Git Error] GITHUB_TOKEN environment variable is missing.")
        return None

    g = Github(token)
    
    try:
        repo = g.get_repo(repo_name)
        
        # 1. Get reference to default branch (main)
        default_branch = repo.default_branch
        sb = repo.get_branch(default_branch)
        
        # 2. Create a unique branch name for the fix
        new_branch_name = f"ai-fix-{os.urandom(4).hex()}"
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=sb.commit.sha)
        print(f"[Git] Created new branch: {new_branch_name}")

        # 3. Check if file exists on main branch first
        try:
            contents = repo.get_contents(file_path, ref=default_branch)
            # Update existing file on the new branch
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=fixed_code,
                sha=contents.sha,
                branch=new_branch_name
            )
            print(f"[Git] Updated existing file: {file_path}")
        except GithubException:
            # File doesn't exist yet on GitHub, create it anew
            repo.create_file(
                path=file_path,
                message=commit_message,
                content=fixed_code,
                branch=new_branch_name
            )
            print(f"[Git] Created new file: {file_path}")

        # 4. Create Pull Request
        pr = repo.create_pull(
            title=commit_message,
            body="🤖 **Automated CI/CD Fix**: Generated and verified by Gemini AI Doctor inside Docker Sandbox.",
            head=new_branch_name,
            base=default_branch
        )
        print(f"[Git] Pull Request created successfully: {pr.html_url}")
        return pr.html_url

    except Exception as e:
        print(f"[Git Error] Failed to create PR: {e}")
        return None
