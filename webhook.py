from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
from main import main as run_agent_repair

app = FastAPI(title="Agentic CI/CD Webhook Listener")

def trigger_repair_pipeline(repo_name: str, commit_sha: str):
    """
    Background task that triggers the Gemini agent workflow.
    In a full production environment, you would use Celery for this.
    """
    print(f"\n[Webhook] Initiating repair pipeline for {repo_name} @ {commit_sha}")
    # Call the main loop from your main.py
    run_agent_repair()

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint configured in GitHub Repo Settings -> Webhooks.
    """
    payload = await request.json()
    
    # Check if this is a workflow run event
    if "workflow_run" in payload:
        action = payload.get("action")
        conclusion = payload["workflow_run"].get("conclusion")
        
        repo_name = payload["repository"]["full_name"]
        commit_sha = payload["workflow_run"]["head_sha"]

        # Only trigger the AI if the automated tests FAILED
        if action == "completed" and conclusion == "failure":
            print(f"[Webhook] Detected CI pipeline failure in {repo_name}!")
            
            # Offload the heavy AI processing to a background task so GitHub gets a fast 200 OK response
            background_tasks.add_task(trigger_repair_pipeline, repo_name, commit_sha)
            
            return {"status": "Repair agent dispatched", "repository": repo_name}
            
        return {"status": f"Ignored event: Workflow {conclusion}"}

    return {"status": "Ignored non-workflow event"}

if __name__ == "__main__":
    print("[API] Starting FastAPI Webhook Listener on port 8000...")
    uvicorn.run("webhook:app", host="0.0.0.0", port=8000)