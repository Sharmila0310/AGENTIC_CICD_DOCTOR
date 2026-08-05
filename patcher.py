import os
from typing import List
from schemas import FileChange

def apply_file_changes(file_changes: List[FileChange]) -> bool:
    success = True
    for change in file_changes:
        if not os.path.exists(change.file_path):
            continue
        content = open(change.file_path, encoding="utf-8").read()
        orig, repl = change.original_code.strip(), change.replacement_code.strip()
        
        if change.original_code in content:
            content = content.replace(change.original_code, change.replacement_code)
        elif orig in content:
            content = content.replace(orig, repl)
        else:
            success = False
            continue
            
        open(change.file_path, "w", encoding="utf-8").write(content)
        print(f"✅ Patched {change.file_path}")
    return success