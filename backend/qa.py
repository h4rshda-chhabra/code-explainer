"""QA Engine — Uses Groq (Llama 3.3 70B) for codebase question answering."""

import os
from typing import List

from groq import Groq


SYSTEM_PROMPT = (
    "You are an expert software engineering assistant that explains "
    "codebases clearly and accurately."
)

CONTEXT_PROMPT_TEMPLATE = """You are an advanced AI Codebase Explainer and Software Engineering Assistant.
Use the codebase context provided below to answer the user's question accurately.
If the context doesn't contain the exact answer but gives enough structural clues, synthesize a helpful explanation based on standard software engineering principles.
If it is completely unrelated to the provided context, state that there is 'Not enough information in the indexed codebase.'
Do NOT generate diagrams, flowcharts, or visual representations for now.

Context:
{context}

Question: {question}
Answer:"""


class QAEngine:
    """Generates answers to codebase questions using Groq's LLM API."""

    def __init__(self, api_key: str = None, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.model = model

    def _build_prompt(self, question: str, context_chunks: List[str]) -> str:
        """Construct the full prompt with retrieved context."""
        context = "\n\n---\n\n".join(context_chunks)
        return CONTEXT_PROMPT_TEMPLATE.format(context=context, question=question)

    def answer_question(self, question: str, context_chunks: List[str]) -> str:
        """Answer a question using retrieved code chunks as context."""
        if not context_chunks:
            return "Not enough information in the codebase."

        prompt = self._build_prompt(question, context_chunks)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API Error: {e}")
            return f"Error: Failed to generate response. {e}"