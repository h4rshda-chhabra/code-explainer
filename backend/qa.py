import os
from typing import List

class QAEngine:
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        from google import genai
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model = model

    def construct_prompt(self, question: str, context_chunks: List[str]) -> str:
        context_text = "\n\n---\n\n".join(context_chunks)
        return f"""You are an advanced AI Codebase Explainer and Software Engineering Assistant.
Use the codebase context provided below to answer the user's question accurately.
If the context doesn't contain the exact answer but gives enough structural clues, synthesize a helpful explanation based on standard software engineering principles.
If it is completely unrelated to the provided context, state that there is 'Not enough information in the indexed codebase.'

Context:
{context_text}

Question: {question}
Answer:"""

    def answer_question(self, question: str, context_chunks: List[str]) -> str:
        if not context_chunks:
            return "Not enough information in the codebase."
            
        prompt = self.construct_prompt(question, context_chunks)
        
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"Error: Failed to generate response from Gemini. {str(e)}"
  