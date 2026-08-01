import os
import shutil
from agent import RepairAgent
from sandbox import SandboxEngine
from git_utils import create_github_pr
from dotenv import load_dotenv

load_dotenv()

def setup_mock_repo():
    workspace = "./mock_workspace"
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    os.makedirs(f"{workspace}/src", exist_ok=True)
    
    # Broken function (ZeroDivisionError on divide by 0)
    with open(f"{workspace}/src/math_utils.py", "w") as f:
        f.write("def divide_numbers(a, b):\n    return a / b\n")
        
    # Failing test file
    with open(f"{workspace}/test_math.py", "w") as f:
        f.write("from src.math_utils import divide_numbers\n\ndef test_divide():\n    assert divide_numbers(10, 2) == 5\n    assert divide_numbers(10, 0) == 0\n")
    
    return os.path.abspath(workspace)

def main(repo_name: str = None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is missing.")
        return

    target_repo = repo_name or os.getenv("GITHUB_REPOSITORY", "Sharmila0310/AGENTIC_CICD_DOCTOR")

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
    with open(f"{workspace}/src/math_utils.py", "r") as f:
        code_context = f.read()

    response = agent.generate_patch(
        error_log=initial_run["logs"],
        ast_context=f"File: src/math_utils.py\n{code_context}"
    )

    print("\n--- [Step 3] Applying generated patches ---")
    patched_file_relative_path = ""
    latest_patched_code = ""
    patch_explanation = "Automated CI Repair"

    for patch in response.patches:
        target_path = os.path.join(workspace, patch.file_path)
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                content = f.read()
            
            updated_content = content.replace(patch.original_code_block, patch.replacement_code_block)
            with open(target_path, "w") as f:
                f.write(updated_content)
            
            patched_file_relative_path = patch.file_path
            latest_patched_code = updated_content
            patch_explanation = patch.explanation
            
            print(f"Applied patch to {patch.file_path}: {patch.explanation}")

    print("\n--- [Step 4] Re-running tests in Sandbox to verify fix ---")
    verification_run = sandbox.run_validation(workspace)
    
    if verification_run["success"]:
        print("\nSUCCESS: Fix verified in Docker Sandbox!")
        print("\n--- [Step 5] Triggering GitHub Pull Request Creation ---")
        
        pr_url = create_github_pr(
            repo_name=target_repo,
            file_path=patched_file_relative_path if patched_file_relative_path else "src/math_utils.py",
            fixed_code=latest_patched_code,
            commit_message=f"🤖 Fix: {patch_explanation}"
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