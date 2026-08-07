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
    event = req.headers.get("X-GitHub-Event")
    action = data.get("action")
    conclusion = data.get("workflow_run", {}).get("conclusion")
    
    print(f"📩 Event: {event} | Action: {action} | Conclusion: {conclusion}")

    # Condition 1: Workflow finished and failed
    is_failed_workflow = (event == "workflow_run" and action == "completed" and conclusion == "failure")
    
    # Condition 2: Direct push event
    is_push_event = (event == "push")

    if is_failed_workflow or is_push_event:
        print("🚀 Condition met! Starting AI repair task...")
        bg.add_task(repair_task)
        return {"status": "repair_started"}
        
    print("⏭️ Event ignored.")
    return {"status": "ignored"}