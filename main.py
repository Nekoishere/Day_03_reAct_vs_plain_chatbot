import os
from dotenv import load_dotenv

load_dotenv()

from src.runtime import (
    DEFAULT_TEST_QUERIES,
    build_llm,
    create_baseline_chatbot,
    create_react_agent,
)


def run_interactive(mode: str):
    llm = build_llm()

    if mode == "baseline":
        print("=== Baseline Football Chatbot (no real-time data) ===")
        bot = create_baseline_chatbot(llm)
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
        agent = create_react_agent(llm, max_steps=6)
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
        raise ValueError(
            f"Unknown mode '{mode}'. Set MODE=baseline, react, compare, or web in .env"
        )


def run_comparison():
    """
    Run both modes on the same fixed queries and print side-by-side results.
    Useful for the lab report evaluation section.
    """
    llm = build_llm()
    bot = create_baseline_chatbot(llm)
    agent = create_react_agent(llm, max_steps=6)

    print("\n" + "=" * 70)
    print("COMPARISON: Baseline Chatbot vs ReAct Agent")
    print("=" * 70)

    for i, query in enumerate(DEFAULT_TEST_QUERIES, 1):
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
    elif mode == "web":
        from src.ui.app import run_server

        run_server()
    else:
        run_interactive(mode)
