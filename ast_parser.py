import ast
import os

def extract_failing_context(file_path: str, target: str = None) -> str:
    if not os.path.exists(file_path):
        return f"Error: {file_path} missing"
    code = open(file_path, encoding="utf-8").read()
    try:
        tree = ast.parse(code)
        if target:
            nodes = [ast.unparse(n) for n in ast.walk(tree) if getattr(n, 'name', None) == target]
            if nodes:
                return f"--- {target} in {file_path} ---\n" + "\n\n".join(nodes)
    except Exception:
        pass
    return f"--- {file_path} ---\n{code}"