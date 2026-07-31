import os
import shutil
from agent import RepairAgent
from sandbox import SandboxEngine
from git_utils import create_github_pr  # <--- Step 5 Integration
from dotenv import load_dotenv  # <-- Add this

load_dotenv()  # <-- Loads the values from your .env file automatically!

api_key = os.getenv("GEMINI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")


# 1. Setup Mock Test Environment
def setup_mock_repo():
    workspace = "./mock_workspace"
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    os.makedirs(f"{workspace}/src", exist_ok=True)
    
    # Broken function (ZeroDivisionError)
    with open(f"{workspace}/src/math_utils.py", "w") as f:
        f.write("def divide_numbers(a, b):\n    return a / b\n")
        
    # Test file that triggers the bug
    with open(f"{workspace}/test_math.py", "w") as f:
        f.write("from src.math_utils import divide_numbers\n\ndef test_divide():\n    assert divide_numbers(10, 0) == 0\n")
    
    return os.path.abspath(workspace)

# 2. Main Execution Loop
def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is missing.")
        return

    workspace = setup_mock_repo()
    sandbox = SandboxEngine()
    agent = RepairAgent(api_key=api_key)

    print("--- [Step 1] Running initial tests in Docker Sandbox ---")
    initial_run = sandbox.run_validation(workspace)
    
    if initial_run["success"]:
        print("Tests are already passing! No repair needed.")
        return

    print("Tests failed as expected. Captured failure logs:")
    print(initial_run["logs"])

    print("\n--- [Step 2] Sending failure logs and code to Gemini ---")
    # Read broken file context
    with open(f"{workspace}/src/math_utils.py", "r") as f:
        code_context = f.read()

    # Get structured fix from Gemini
    response = agent.generate_patch(
        error_log=initial_run["logs"],
        ast_context=f"File: src/math_utils.py\n{code_context}"
    )

    print("\n--- [Step 3] Applying generated patches ---")
    patched_file_relative_path = ""
    latest_patched_code = ""

    for patch in response.patches:
        target_path = os.path.join(workspace, patch.file_path)
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                content = f.read()
            
            # Apply string replacement
            updated_content = content.replace(patch.original_code_block, patch.replacement_code_block)
            with open(target_path, "w") as f:
                f.write(updated_content)
            
            # Store values for PR step
            patched_file_relative_path = patch.file_path
            latest_patched_code = updated_content
            
            print(f"Applied patch to {patch.file_path}: {patch.explanation}")

    print("\n--- [Step 4] Re-running tests in Sandbox to verify fix ---")
    verification_run = sandbox.run_validation(workspace)
    
    if verification_run["success"]:
        print("\nSUCCESS: Fix verified in Docker Sandbox!")
        
        # --- [Step 5] Creating GitHub Branch and Opening Pull Request ---
        print("\n--- [Step 5] Triggering GitHub Pull Request Creation ---")
        
        # Set your GitHub repository details here
        repo_name = os.getenv("GITHUB_REPOSITORY", "YOUR_USERNAME/AGENTIC_CICD_DOCTOR")
        
        pr_url = create_github_pr(
            repo_name=repo_name,
            file_path=patched_file_relative_path if patched_file_relative_path else "src/math_utils.py",
            fixed_code=latest_patched_code,
            commit_message=f"🤖 Fix: {response.explanation if hasattr(response, 'explanation') else 'Automated CI Repair'}"
        )
        
        if pr_url:
            print(f"🚀 Pull Request successfully published at: {pr_url}")
        else:
            print("⚠️ PR creation skipped or failed. Check GITHUB_TOKEN environment variable.")

    else:
        print("\nFAILED: Patch did not fix the issue.")
        print(verification_run["logs"])

if __name__ == "__main__":
    main()