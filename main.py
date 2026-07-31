import os
import shutil
from agent import RepairAgent
from sandbox import SandboxEngine

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

    print("\n--- [Step 2] Sending failure logs and code to Gemini 2.5 Flash ---")
    # Read broken file context
    with open(f"{workspace}/src/math_utils.py", "r") as f:
        code_context = f.read()

    # Get structured fix from Gemini
    response = agent.generate_patch(
        error_log=initial_run["logs"],
        ast_context=f"File: src/math_utils.py\n{code_context}"
    )

    print("\n--- [Step 3] Applying generated patches ---")
    for patch in response.patches:
        target_path = os.path.join(workspace, patch.file_path)
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                content = f.read()
            
            # Apply string replacement
            updated_content = content.replace(patch.original_code_block, patch.replacement_code_block)
            with open(target_path, "w") as f:
                f.write(updated_content)
            print(f"Applied patch to {patch.file_path}: {patch.explanation}")

    print("\n--- [Step 4] Re-running tests in Sandbox to verify fix ---")
    verification_run = sandbox.run_validation(workspace)
    
    if verification_run["success"]:
        print("SUCCESS: Fix verified in Docker Sandbox! Ready to open Pull Request.")
    else:
        print("FAILED: Patch did not fix the issue.")
        print(verification_run["logs"])

if __name__ == "__main__":
    main()