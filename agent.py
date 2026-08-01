import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from schemas import AgentResponse

# Load API key from .env automatically
load_dotenv()

class RepairAgent:
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY is missing! Make sure it's set in your .env file.")
            
        self.client = genai.Client(api_key=key)
        # Using gemini-2.5-flash (valid model string for Google GenAI SDK)
        self.model = "gemini-2.5-flash"

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