import os
from fastapi import FastAPI, Request, BackgroundTasks
from agent import RepairAgent
from ast_parser import extract_failing_context
from patcher import apply_file_changes
from sandbox import DockerSandbox

app = FastAPI()

def repair_task(repo_path: str = "."):
    sandbox = DockerSandbox()
    res = sandbox.run_pytest(repo_path)
    if res["passed"]: return
    
    target = res["failed_file"] or "main.py"
    ctx = extract_failing_context(target)
    patch = RepairAgent().generate_patch(res["logs"], ctx)
    apply_file_changes(patch.file_changes)

@app.post("/webhook/github")
async def handle_webhook(req: Request, bg: BackgroundTasks):
    data = await req.json()
    if data.get("action") == "completed" and data.get("workflow_run", {}).get("conclusion") == "failure":
        bg.add_task(repair_task)
        return {"status": "repair_started"}
    return {"status": "ignored"}