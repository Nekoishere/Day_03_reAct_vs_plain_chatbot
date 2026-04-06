from typing import Dict, Any

from src.core.llm_provider import LLMProvider
from src.telemetry.metrics import tracker


DEFAULT_BASELINE_SYSTEM_PROMPT = (
    "You are a football history assistant. "
    "Answer directly in Vietnamese, concise and factual. "
    "If uncertain, explicitly mention uncertainty."
)


class BaselineChatbot:
    def __init__(self, llm: LLMProvider, system_prompt: str = DEFAULT_BASELINE_SYSTEM_PROMPT):
        self.llm = llm
        self.system_prompt = system_prompt

    def ask(self, question: str, scenario: str = "baseline") -> Dict[str, Any]:
        result = self.llm.generate(question, system_prompt=self.system_prompt)
        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
            scenario=scenario,
        )
        return result
