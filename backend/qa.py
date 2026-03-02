from abc import ABC, abstractmethod
from typing import List
import os

class LLMProvider(ABC):
    @abstractmethod
    def generate_answer(self, prompt: str) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        import openai
        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate_answer(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content

class MockProvider(LLMProvider):
    def generate_answer(self, prompt: str) -> str:
        return "I am a mock response. Please provide an OpenAI API key for real answers."

class QAEngine:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def construct_prompt(self, question: str, context_chunks: List[str]) -> str:
        context_text = "\n\n---\n\n".join(context_chunks)
        prompt = f"""You are a DevOps assistant.
Answer the question only using the context provided below.
If the answer is not present in the context, say 'Not enough information in the codebase.'

Context:
{context_text}

Question: {question}
Answer:"""
        return prompt

    def answer_question(self, question: str, context_chunks: List[str]) -> str:
        if not context_chunks:
            return "Not enough information in the codebase."
            
        prompt = self.construct_prompt(question, context_chunks)
        return self.llm.generate_answer(prompt)
