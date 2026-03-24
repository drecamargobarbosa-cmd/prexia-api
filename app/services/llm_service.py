import os
from openai import OpenAI


class LLMService:

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada no ambiente.")

        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            return f"Erro ao chamar LLM: {str(e)}"
