import sys
import os
import subprocess
import uvicorn
from dotenv import load_dotenv
from agent import RepairAgent
from ast_parser import extract_failing_context
from patcher import apply_file_changes
from sandbox import DockerSandbox
from github_service import GitHubPRService

load_dotenv()

def get_local_repo_name() -> str:
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        parts = url.rstrip(".git").replace(":", "/").split("/")
        return f"{parts[-2]}/{parts[-1]}"
    except Exception:
        return None

def run_pipeline(repo_path: str = "."):
    print("🤖 Running CI Doctor...")
    repo_name = get_local_repo_name()
    if repo_name:
        print(f"📦 Auto-detected repository: {repo_name}")
        
    sandbox = DockerSandbox()
    res = sandbox.run_pytest(repo_path)
    
    if res["passed"]:
        return print("✅ All tests passed!")

    target = res["failed_file"] or "calculator.py"
    ctx = extract_failing_context(target)
    patch = RepairAgent().generate_patch(res["logs"], ctx)
    
    print(f"🧠 Thought: {patch.thought_process}")
    
    if apply_file_changes(patch.file_changes) and sandbox.run_pytest(repo_path)["passed"]:
        print("🎉 Fix Verified in Sandbox!")
        if repo_name and os.getenv("GITHUB_TOKEN"):
            url = GitHubPRService().create_pr(
                repo_name, 
                "main", 
                [c.model_dump() for c in patch.file_changes], 
                patch.thought_process
            )
            print(f"✨ Automated PR Created: {url}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        uvicorn.run("webhook:app", host="0.0.0.0", port=8000)
    else:
        run_pipeline()