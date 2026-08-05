import sys, os, uvicorn
from dotenv import load_dotenv
from agent import RepairAgent
from ast_parser import extract_failing_context
from patcher import apply_file_changes
from sandbox import DockerSandbox
from github_service import GitHubPRService

load_dotenv()

def run_pipeline(repo_path: str = ".", repo_name: str = None):
    print("🤖 Running CI Doctor...")
    sandbox = DockerSandbox()
    res = sandbox.run_pytest(repo_path)
    
    if res["passed"]:
        return print("✅ All tests passed!")

    target = res["failed_file"] or "calculator.py"
    ctx = extract_failing_context(target)
    patch = RepairAgent().generate_patch(res["logs"], ctx)
    
    print(f"🧠 Thought: {patch.thought_process}")
    if apply_file_changes(patch.file_changes) and sandbox.run_pytest(repo_path)["passed"]:
        print("🎉 Fix Verified!")
        if repo_name and os.getenv("GITHUB_TOKEN"):
            url = GitHubPRService().create_pr(repo_name, "main", [c.model_dump() for c in patch.file_changes], patch.thought_process)
            print(f"✨ PR Created: {url}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        uvicorn.run("webhook:app", host="0.0.0.0", port=8000)
    else:
        run_pipeline()