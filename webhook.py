import os
import subprocess
from fastapi import FastAPI, Request, BackgroundTasks
from agent import RepairAgent
from ast_parser import extract_failing_context
from patcher import apply_file_changes
from sandbox import DockerSandbox
from github_service import GitHubPRService

app = FastAPI()

def get_local_repo_name() -> str:
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        parts = url.rstrip(".git").replace(":", "/").split("/")
        return f"{parts[-2]}/{parts[-1]}"
    except Exception:
        return None

def repair_task(repo_path: str = "."):
    print("🚀 Triggering AI Repair Task...")
    repo_name = get_local_repo_name()
    sandbox = DockerSandbox()
    res = sandbox.run_pytest(repo_path)
    
    if res["passed"]: 
        print("✅ All tests passed. No fix needed.")
        return
    
    target = res["failed_file"] or "calculator.py"
    ctx = extract_failing_context(target)
    patch = RepairAgent().generate_patch(res["logs"], ctx)
    apply_file_changes(patch.file_changes)
    print("🛠️ Applied fix locally.")

    try:
        if repo_name and os.getenv("GITHUB_TOKEN"):
            gh = GitHubPRService()
            pr_url = gh.create_pr(
                repo_name,
                "main",
                [c.model_dump() for c in patch.file_changes],
                patch.thought_process
            )
            print(f"✨ PR Created Successfully: {pr_url}")
    except Exception as e:
        print(f"❌ Failed to create PR on GitHub: {e}")

@app.post("/webhook/github")
async def handle_webhook(req: Request, bg: BackgroundTasks):
    data = await req.json()
    event = req.headers.get("X-GitHub-Event")
    action = data.get("action")
    conclusion = data.get("workflow_run", {}).get("conclusion")
    
    print(f"📩 Event: {event} | Action: {action} | Conclusion: {conclusion}")

    is_failed_workflow = (event == "workflow_run" and action == "completed" and conclusion == "failure")

    if is_failed_workflow:
        print("🚀 Condition met! Starting AI repair task...")
        bg.add_task(repair_task)
        return {"status": "repair_started"}
        
    print("⏭️ Event ignored.")
    return {"status": "ignored"}