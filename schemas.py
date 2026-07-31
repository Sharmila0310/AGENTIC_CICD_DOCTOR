from pydantic import BaseModel, Field

class PatchTarget(BaseModel):
    file_path: str = Field(description="Relative path to the broken file in the repo.")
    original_code_block: str = Field(description="Exact snippet of the broken code to be replaced.")
    replacement_code_block: str = Field(description="The new, fixed code snippet.")
    explanation: str = Field(description="Brief technical reasoning for this fix.")

class AgentResponse(BaseModel):
    patches: list[PatchTarget] = Field(description="A list of code patches required to fix the build.")