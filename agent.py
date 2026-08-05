import ollama
from schemas import AgentResponse

class RepairAgent:
    def __init__(self, model: str = "qwen2.5-coder:7b"):
        self.model = model

    def generate_patch(self, error_log: str, ast_context: str) -> AgentResponse:
        prompt = f"Fix this CI failure.\nError:\n{error_log}\nContext:\n{ast_context}"
        res = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a CI repair bot. Output strictly valid JSON matching the schema with 'thought_process' and 'file_changes' (list of file_path, original_code, replacement_code)."},
                {"role": "user", "content": prompt}
            ],
            format="json"
        )
        return AgentResponse.model_validate_json(res['message']['content'])