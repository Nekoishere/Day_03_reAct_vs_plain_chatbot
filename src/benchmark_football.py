import argparse
import json
import os
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.chatbot.baseline import BaselineChatbot
from src.core.llm_provider import LLMProvider
from src.evaluation.football_eval import FOOTBALL_DATASET, EvalRecord, keyword_score, avg_score
from src.telemetry.metrics import tracker
from src.tools.football_history import get_football_tools

def create_provider(provider_name: str, model_name: str, api_key: str = "") -> LLMProvider:
    provider_name = provider_name.lower()
    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(model_name=model_name, api_key=api_key)
    if provider_name == "google":
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(model_name=model_name, api_key=api_key)
    if provider_name == "local":
        from src.core.local_provider import LocalProvider

        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)
    raise ValueError("Unsupported provider. Use: openai | google | local")


def run_baseline(llm: LLMProvider) -> Dict[str, Any]:
    bot = BaselineChatbot(llm)
    records: List[EvalRecord] = []

    for sample in FOOTBALL_DATASET:
        result = bot.ask(sample.question, scenario="baseline")
        answer = result.get("content", "")
        score = keyword_score(answer, sample.must_have_keywords)
        records.append(
            EvalRecord(question=sample.question, answer=answer, score=score, method="baseline")
        )

    metrics = tracker.summarize("baseline")
    metrics["avg_keyword_score"] = avg_score(records)
    return {"records": [r.to_dict() for r in records], "metrics": metrics}


def run_react(llm: LLMProvider) -> Dict[str, Any]:
    agent = ReActAgent(llm=llm, tools=get_football_tools(), max_steps=5)
    records: List[EvalRecord] = []
    step_counts: List[int] = []

    for sample in FOOTBALL_DATASET:
        answer = agent.run(sample.question)
        score = keyword_score(answer, sample.must_have_keywords)
        records.append(
            EvalRecord(question=sample.question, answer=answer, score=score, method="react")
        )
        step_counts.append(len(agent.history))

    metrics = tracker.summarize("react")
    metrics["avg_keyword_score"] = avg_score(records)
    metrics["avg_steps"] = round(sum(step_counts) / len(step_counts), 2) if step_counts else 0
    return {"records": [r.to_dict() for r in records], "metrics": metrics}


def print_report(title: str, result: Dict[str, Any]):
    print(f"\n===== {title} =====")
    for item in result["records"]:
        print(f"\nQ: {item['question']}")
        print(f"A: {item['answer']}")
        print(f"Score: {item['score']}")

    print("\nMetrics:")
    for key, value in result["metrics"].items():
        print(f"- {key}: {value}")


def build_comparison(baseline_result: Dict[str, Any], react_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "baseline_avg_keyword_score": baseline_result["metrics"]["avg_keyword_score"],
        "react_avg_keyword_score": react_result["metrics"]["avg_keyword_score"],
        "baseline_total_tokens": baseline_result["metrics"]["total_tokens"],
        "react_total_tokens": react_result["metrics"]["total_tokens"],
        "baseline_avg_latency_ms": baseline_result["metrics"]["avg_latency_ms"],
        "react_avg_latency_ms": react_result["metrics"]["avg_latency_ms"],
        "react_avg_steps": react_result["metrics"].get("avg_steps", 0),
    }


def write_reports(
    output_dir: str,
    provider: str,
    model: str,
    baseline_result: Dict[str, Any],
    react_result: Dict[str, Any],
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    comparison = build_comparison(baseline_result, react_result)

    json_path = os.path.join(output_dir, f"football_benchmark_{provider}_{ts}.json")
    md_path = os.path.join(output_dir, f"football_benchmark_{provider}_{ts}.md")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "baseline": baseline_result,
        "react": react_result,
        "comparison": comparison,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    md_lines = [
        "# Football Benchmark Report",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Provider: `{provider}`",
        f"- Model: `{model}`",
        "",
        "## Comparison Summary",
        "",
        "| Metric | Baseline | ReAct |",
        "|---|---:|---:|",
        f"| Avg keyword score | {comparison['baseline_avg_keyword_score']} | {comparison['react_avg_keyword_score']} |",
        f"| Total tokens | {comparison['baseline_total_tokens']} | {comparison['react_total_tokens']} |",
        f"| Avg latency (ms) | {comparison['baseline_avg_latency_ms']} | {comparison['react_avg_latency_ms']} |",
        f"| Avg steps | - | {comparison['react_avg_steps']} |",
        "",
        "## Baseline QA",
        "",
    ]

    for row in baseline_result["records"]:
        md_lines.extend(
            [
                f"### Q: {row['question']}",
                f"- Score: `{row['score']}`",
                f"- A: {row['answer']}",
                "",
            ]
        )

    md_lines.extend(["## ReAct QA", ""])
    for row in react_result["records"]:
        md_lines.extend(
            [
                f"### Q: {row['question']}",
                f"- Score: `{row['score']}`",
                f"- A: {row['answer']}",
                "",
            ]
        )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return {"json": json_path, "md": md_path}


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Benchmark Baseline vs ReAct for football history topic.")
    parser.add_argument("--provider", default=os.getenv("DEFAULT_PROVIDER", "openai"), choices=["openai", "google", "local"])
    parser.add_argument("--model", default=os.getenv("DEFAULT_MODEL", "gpt-4o"))
    parser.add_argument("--output-dir", default="report/benchmark_runs")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
    elif args.provider == "google":
        api_key = os.getenv("GEMINI_API_KEY", "")
    else:
        api_key = ""

    llm = create_provider(args.provider, args.model, api_key=api_key)
    tracker.reset()

    baseline_result = run_baseline(llm)
    react_result = run_react(llm)

    print_report("Baseline", baseline_result)
    print_report("ReAct", react_result)
    comparison = build_comparison(baseline_result, react_result)

    print("\n===== Comparison =====")
    print(f"- baseline avg_keyword_score: {comparison['baseline_avg_keyword_score']}")
    print(f"- react avg_keyword_score: {comparison['react_avg_keyword_score']}")
    print(f"- baseline total_tokens: {comparison['baseline_total_tokens']}")
    print(f"- react total_tokens: {comparison['react_total_tokens']}")
    print(f"- baseline avg_latency_ms: {comparison['baseline_avg_latency_ms']}")
    print(f"- react avg_latency_ms: {comparison['react_avg_latency_ms']}")
    print(f"- react avg_steps: {comparison['react_avg_steps']}")

    if not args.no_save:
        paths = write_reports(
            output_dir=args.output_dir,
            provider=args.provider,
            model=args.model,
            baseline_result=baseline_result,
            react_result=react_result,
        )
        print("\n===== Saved Reports =====")
        print(f"- JSON: {paths['json']}")
        print(f"- Markdown: {paths['md']}")


if __name__ == "__main__":
    main()
