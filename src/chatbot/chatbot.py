from typing import List, Dict
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

SYSTEM_PROMPT = """You are a knowledgeable football assistant.
Answer questions about football matches, scores, teams, players, and statistics.
Important: You rely only on your training data — you do NOT have access to real-time or
live information. If asked about live scores or very recent events, clearly say you don't
have access to real-time data."""


class BaselineChatbot:
    """
    A simple chatbot that wraps an LLMProvider with no external tools.
    All answers come from the LLM's internal knowledge — no live data.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.history: List[Dict[str, str]] = []

    def chat(self, user_input: str) -> str:
        logger.log_event("CHATBOT_INPUT", {"input": user_input})

        # Build context from last 6 turns
        context = ""
        for turn in self.history[-6:]:
            context += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
        context += f"User: {user_input}"

        result = self.llm.generate(context, system_prompt=SYSTEM_PROMPT)
        answer = result["content"]

        logger.log_event("CHATBOT_OUTPUT", {
            "output": answer,
            "latency_ms": result["latency_ms"],
            "usage": result["usage"],
        })

        self.history.append({"user": user_input, "assistant": answer})
        return answer

    def reset(self):
        self.history = []
