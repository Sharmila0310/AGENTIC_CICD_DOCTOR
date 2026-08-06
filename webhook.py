import os
from fastapi import FastAPI, Request, BackgroundTasks
from agent import RepairAgent
from ast_parser import extract_failing_context
from patcher import apply_file_changes
from sandbox import DockerSandbox
from github_service import GitHubPRService

app = FastAPI()

def repair_task(repo_path: str = "."):
    print("🚀 Triggering AI Repair Task...")
    sandbox = DockerSandbox()
    res = sandbox.run_pytest(repo_path)
    
    if res["passed"]: 
        print("✅ All tests passed. No fix needed.")
        return
    
    target = res["failed_file"] or "main.py"
    ctx = extract_failing_context(target)
    patch = RepairAgent().generate_patch(res["logs"], ctx)
    apply_file_changes(patch.file_changes)
    print("🛠️ Applied fix locally.")

    # -------------------------------------------------------------
    # 🚀 STEP ADDED: Create branch, push fix, and open PR on GitHub!
    # -------------------------------------------------------------
    try:
        gh = GitHubService()
        pr_url = gh.create_pull_request(
            branch_name="fix/ci-doctor-auto-repair",
            commit_message="🤖 [CI Doctor] Auto-fix failing tests",
            pr_title="🤖 Fix: Automated CI Repair",
            pr_body=f"### Automated Patch by AI Doctor\n\nReasoning:\n{patch.reasoning}"
        )
        print(f"✨ PR Created Successfully: {pr_url}")
    except Exception as e:
        print(f"❌ Failed to create PR on GitHub: {e}")


@app.post("/webhook/github")
async def handle_webhook(req: Request, bg: BackgroundTasks):
    data = await req.json()
    
    # Debug print event details
    event = req.headers.get("X-GitHub-Event")
    print(f"📩 Webhook event: {event}, action: {data.get('action')}")

    # Trigger on workflow failure OR direct push
    if data.get("action") == "completed" and data.get("workflow_run", {}).get("conclusion") == "failure":
        bg.add_task(repair_task)
        return {"status": "repair_started"}
        
    return {"status": "ignored"}