from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from main import main as run_agent_repair

app = FastAPI(title="Agentic CI/CD Webhook Listener")

def trigger_repair_pipeline(repo_name: str, commit_sha: str):
    print(f"\n[Webhook] Initiating repair pipeline for {repo_name} @ {commit_sha}")
    run_agent_repair(repo_name=repo_name)

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    
    # 1. Handle workflow_run events (from GitHub Actions)
    if "workflow_run" in payload:
        action = payload.get("action")
        conclusion = payload["workflow_run"].get("conclusion")
        repo_name = payload["repository"]["full_name"]
        commit_sha = payload["workflow_run"]["head_sha"]

        if action == "completed" and conclusion == "failure":
            print(f"[Webhook] Detected CI pipeline failure in {repo_name}!")
            background_tasks.add_task(trigger_repair_pipeline, repo_name, commit_sha)
            return {"status": "Repair agent dispatched", "repository": repo_name}
            
        return {"status": f"Ignored workflow status: {conclusion}"}

    # 2. Handle push events (for testing/redeliver fallback)
    if "commits" in payload and "repository" in payload:
        repo_name = payload["repository"]["full_name"]
        commit_sha = payload.get("after", "head")
        print(f"[Webhook] Push event received for {repo_name}. Dispatching agent for testing...")
        background_tasks.add_task(trigger_repair_pipeline, repo_name, commit_sha)
        return {"status": "Repair agent dispatched via push event", "repository": repo_name}

    return {"status": "Ignored non-targeted event"}

if __name__ == "__main__":
    print("[API] Starting FastAPI Webhook Listener on port 8000...")
    uvicorn.run("webhook:app", host="0.0.0.0", port=8000)