from pydantic import BaseModel
from typing import List

class FileChange(BaseModel):
    file_path: str
    original_code: str
    replacement_code: str

class AgentResponse(BaseModel):
    thought_process: str
    file_changes: List[FileChange]