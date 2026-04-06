import os
from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.chatbot.chatbot import BaselineChatbot
from src.agent.agent import ReActAgent
from src.tools.football_tools import FOOTBALL_TOOLS


def build_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")

    if provider == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "google":
        return GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    else:
        raise ValueError(f"Unknown provider: {provider}. Set DEFAULT_PROVIDER=openai or google in .env")


def run_interactive(mode: str):
    llm = build_llm()

    if mode == "baseline":
        print("=== Baseline Football Chatbot (no real-time data) ===")
        bot = BaselineChatbot(llm)
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not user_input or user_input.lower() in ("exit", "quit"):
                break
            answer = bot.chat(user_input)
            print(f"\nChatbot: {answer}")

    elif mode == "react":
        print("=== ReAct Football Agent (real-time web search) ===")
        agent = ReActAgent(llm, tools=FOOTBALL_TOOLS, max_steps=6)
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            if not user_input or user_input.lower() in ("exit", "quit"):
                break
            answer = agent.run(user_input)
            print(f"\nAgent: {answer}")

    else:
        raise ValueError(f"Unknown mode '{mode}'. Set MODE=baseline or MODE=react in .env")


def run_comparison():
    """
    Run both modes on the same fixed queries and print side-by-side results.
    Useful for the lab report evaluation section.
    """
    TEST_QUERIES = [
        "What are the live football scores right now?",
        "Who are the top 3 scorers in the Premier League this season?",
        "What are the current Premier League standings?",
        "Show me the recent results for Manchester United.",
        "What is the lineup for Real Madrid today?",
    ]

    llm = build_llm()
    bot = BaselineChatbot(llm)
    agent = ReActAgent(llm, tools=FOOTBALL_TOOLS, max_steps=6)

    print("\n" + "=" * 70)
    print("COMPARISON: Baseline Chatbot vs ReAct Agent")
    print("=" * 70)

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Query {i}] {query}")
        print("-" * 70)

        print("\n[BASELINE]")
        print(bot.chat(query))

        print("\n[REACT AGENT]")
        print(agent.run(query))

        print("=" * 70)


if __name__ == "__main__":
    mode = os.getenv("MODE", "react").strip().lower()

    if mode == "compare":
        run_comparison()
    else:
        run_interactive(mode)
