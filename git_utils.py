import os
from github import Github

def create_github_pr(repo_name: str, file_path: str, fixed_code: str, commit_message: str):
    """
    Pushes fixed code to a new branch on GitHub and opens a Pull Request.
    """
    # 1. Authenticate with GitHub using your token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("[Git] GITHUB_TOKEN not set. Skipping PR creation.")
        return

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    # 2. Get the default branch (e.g., 'main') and its latest commit
    main_branch = repo.get_branch("main")
    base_sha = main_branch.commit.sha

    # 3. Create a unique fix branch name
    import time
    new_branch_name = f"fix/ai-repair-{int(time.time())}"
    repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_sha)

    # 4. Fetch the existing file content to get its blob SHA
    contents = repo.get_contents(file_path, ref=new_branch_name)

    # 5. Commit the fixed code to the new branch
    repo.update_file(
        path=file_path,
        message=commit_message,
        content=fixed_code,
        sha=contents.sha,
        branch=new_branch_name
    )

    # 6. Open the Pull Request on GitHub
    pr_body = (
        "### 🤖 Automated AI Doctor Repair\n\n"
        f"**Reason for Fix:** {commit_message}\n\n"
        "**Verification:** This fix was automatically verified inside an isolated Docker sandbox running `pytest`."
    )
    
    pr = repo.create_pull(
        title=f"🤖 Fix: CI Pipeline Error in {file_path}",
        body=pr_body,
        head=new_branch_name,
        base="main"
    )

    print(f"[Git] Successfully created PR: {pr.html_url}")
    return pr.html_url