import os
from google import genai
from google.genai import types
from schemas import AgentResponse

class RepairAgent:
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=key)
        # Use a universally supported model name
        self.model = "gemini-1.5-flash"  # or "gemini-2.0-flash"

    def generate_patch(self, error_log: str, ast_context: str) -> AgentResponse:
        prompt = f"""
        Analyze the CI failure and the provided source code context.
        Generate the precise code replacements needed to fix the broken tests.
        
        Error Log:
        {error_log}
        
        Code Context:
        {ast_context}
        """
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=AgentResponse,
            )
        )
        
        return AgentResponse.model_validate_json(response.text)