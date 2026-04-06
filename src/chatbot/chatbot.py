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
    Maintains full conversation history across turns.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        # Store messages in OpenAI format so history is passed correctly
        self.history: List[Dict[str, str]] = []

    def chat(self, user_input: str) -> str:
        logger.log_event("CHATBOT_INPUT", {"input": user_input})

        self.history.append({"role": "user", "content": user_input})

        # Build full messages list: system + all history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        result = self.llm.generate(prompt="", messages=messages)
        answer = result["content"]

        logger.log_event("CHATBOT_OUTPUT", {
            "output": answer,
            "latency_ms": result["latency_ms"],
            "usage": result["usage"],
        })

        self.history.append({"role": "assistant", "content": answer})
        return answer

    def reset(self):
        self.history = []
