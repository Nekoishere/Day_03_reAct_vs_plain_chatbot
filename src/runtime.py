import os

from src.agent.agent import ReActAgent
from src.chatbot.chatbot import BaselineChatbot
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.tools.football_tools import FOOTBALL_TOOLS


DEFAULT_TEST_QUERIES = [
    "What are the live football scores right now?",
    "Who are the top 3 scorers in the Premier League this season?",
    "What are the current Premier League standings?",
    "Show me the recent results for Manchester United.",
    "What is the lineup for Real Madrid today?",
]


def require_env(var_name: str) -> str:
    value = os.getenv(var_name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value


def build_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
    model = os.getenv("DEFAULT_MODEL", "gpt-4o").strip()

    if provider == "openai":
        return OpenAIProvider(
            model_name=model,
            api_key=require_env("OPENAI_API_KEY"),
        )

    if provider in ("google", "gemini"):
        return GeminiProvider(
            model_name=model,
            api_key=require_env("GEMINI_API_KEY"),
        )

    raise ValueError(
        f"Unknown provider: {provider}. Set DEFAULT_PROVIDER=openai or google in .env"
    )


def create_baseline_chatbot(llm=None) -> BaselineChatbot:
    return BaselineChatbot(llm or build_llm())


def create_react_agent(llm=None, max_steps: int = 6) -> ReActAgent:
    return ReActAgent(llm or build_llm(), tools=FOOTBALL_TOOLS, max_steps=max_steps)
