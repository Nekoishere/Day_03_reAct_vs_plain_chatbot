import argparse
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.chatbot.baseline import BaselineChatbot
from src.core.llm_provider import LLMProvider
from src.evaluation.football_eval import (
    FOOTBALL_DATASET,
    EvalRecord,
    EvalSample,
    keyword_score,
    avg_score,
    load_dataset_from_json,
    build_dataset_from_questions,
    interactive_collect_samples,
)
from src.telemetry.logger import logger
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


def score_or_none(answer: str, sample: EvalSample) -> Optional[float]:
    if not sample.must_have_keywords:
        return None
    return keyword_score(answer, sample.must_have_keywords)


def run_baseline(llm: LLMProvider, dataset: List[EvalSample], scenario: str) -> Dict[str, Any]:
    bot = BaselineChatbot(llm)
    records: List[EvalRecord] = []

    for sample in dataset:
        result = bot.ask(sample.question, scenario=scenario)
        answer = result.get("content", "")
        score = score_or_none(answer, sample)
        records.append(
            EvalRecord(question=sample.question, answer=answer, score=score, method="baseline")
        )

    metrics = tracker.summarize(scenario)
    metrics["avg_keyword_score"] = avg_score(records)
    metrics["scored_questions"] = sum(1 for r in records if r.score is not None)
    return {"records": [r.to_dict() for r in records], "metrics": metrics}


def run_react(
    llm: LLMProvider,
    dataset: List[EvalSample],
    scenario: str,
    react_max_steps: int,
    tool_mode: str,
) -> Dict[str, Any]:
    agent = ReActAgent(
        llm=llm,
        tools=get_football_tools(tool_mode=tool_mode),
        max_steps=react_max_steps,
        metric_scenario=scenario,
    )
    records: List[EvalRecord] = []
    step_counts: List[int] = []

    for sample in dataset:
        answer = agent.run(sample.question)
        score = score_or_none(answer, sample)
        records.append(
            EvalRecord(question=sample.question, answer=answer, score=score, method="react")
        )
        step_counts.append(len(agent.history))

    metrics = tracker.summarize(scenario)
    metrics["avg_keyword_score"] = avg_score(records)
    metrics["scored_questions"] = sum(1 for r in records if r.score is not None)
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


def print_single_mode_summary(mode: str, result: Dict[str, Any]):
    print(f"\n===== {mode.upper()} Summary =====")
    for key, value in result["metrics"].items():
        print(f"- {key}: {value}")


def resolve_dataset(args: argparse.Namespace) -> List[EvalSample]:
    if args.ui_input:
        data = interactive_collect_samples()
        if not data:
            raise ValueError("Bạn chưa nhập câu hỏi nào trong UI.")
        return data
    if args.dataset_file:
        return load_dataset_from_json(args.dataset_file)
    if args.question:
        data = build_dataset_from_questions(args.question)
        if not data:
            raise ValueError("--question được truyền nhưng rỗng.")
        return data
    return FOOTBALL_DATASET


def write_reports(
    output_dir: str,
    provider: str,
    model: str,
    metadata: Dict[str, Any],
    baseline_result: Optional[Dict[str, Any]] = None,
    react_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_tag = metadata.get("run_tag", "default")
    comparison = None
    if baseline_result is not None and react_result is not None:
        comparison = build_comparison(baseline_result, react_result)

    json_path = os.path.join(output_dir, f"football_benchmark_{provider}_{run_tag}_{ts}.json")
    md_path = os.path.join(output_dir, f"football_benchmark_{provider}_{run_tag}_{ts}.md")

    payload = {
        "generated_at": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "metadata": metadata,
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
        f"- Run tag: `{metadata.get('run_tag', 'default')}`",
        f"- Mode: `{metadata.get('mode', 'both')}`",
        f"- Dataset source: `{metadata.get('dataset_source', 'default')}`",
        f"- Dataset size: `{metadata.get('dataset_size', 0)}`",
        f"- Baseline version: `{metadata.get('baseline_version', 'v1')}`",
        f"- ReAct version: `{metadata.get('react_version', 'v1')}`",
        f"- Toolset version: `{metadata.get('toolset_version', 'v1')}`",
        f"- Dataset version: `{metadata.get('dataset_version', 'v1')}`",
        "",
    ]

    if comparison is not None:
        md_lines.extend(
            [
                "## Comparison Summary",
                "",
                "| Metric | Baseline | ReAct |",
                "|---|---:|---:|",
                f"| Avg keyword score | {comparison['baseline_avg_keyword_score']} | {comparison['react_avg_keyword_score']} |",
                f"| Total tokens | {comparison['baseline_total_tokens']} | {comparison['react_total_tokens']} |",
                f"| Avg latency (ms) | {comparison['baseline_avg_latency_ms']} | {comparison['react_avg_latency_ms']} |",
                f"| Avg steps | - | {comparison['react_avg_steps']} |",
                "",
            ]
        )

    if baseline_result is not None:
        md_lines.extend(["## Baseline QA", ""])
    for row in (baseline_result or {}).get("records", []):
        score_text = "N/A" if row["score"] is None else str(row["score"])
        md_lines.extend(
            [
                f"### Q: {row['question']}",
                f"- Score: `{score_text}`",
                f"- A: {row['answer']}",
                "",
            ]
        )

    if react_result is not None:
        md_lines.extend(["## ReAct QA", ""])
    for row in (react_result or {}).get("records", []):
        score_text = "N/A" if row["score"] is None else str(row["score"])
        md_lines.extend(
            [
                f"### Q: {row['question']}",
                f"- Score: `{score_text}`",
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
    parser.add_argument("--mode", default="both", choices=["baseline", "react", "both"])
    parser.add_argument("--dataset-file", default="")
    parser.add_argument("--question", action="append", default=[])
    parser.add_argument("--ui-input", action="store_true")
    parser.add_argument("--output-dir", default="report/benchmark_runs")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--run-tag", default=os.getenv("RUN_TAG", "v1"))
    parser.add_argument("--baseline-version", default="baseline_v1")
    parser.add_argument("--react-version", default="react_v1")
    parser.add_argument("--toolset-version", default="tools_v1")
    parser.add_argument("--dataset-version", default="dataset_v1")
    parser.add_argument("--react-max-steps", type=int, default=5)
    parser.add_argument("--tool-mode", default="hybrid", choices=["offline", "web", "hybrid"])
    args = parser.parse_args()

    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
    elif args.provider == "google":
        api_key = os.getenv("GEMINI_API_KEY", "")
    else:
        api_key = ""

    llm = create_provider(args.provider, args.model, api_key=api_key)
    tracker.reset()
    dataset = resolve_dataset(args)

    dataset_source = "default"
    if args.ui_input:
        dataset_source = "ui_input"
    elif args.dataset_file:
        dataset_source = "dataset_file"
    elif args.question:
        dataset_source = "cli_question"

    metadata = {
        "mode": args.mode,
        "run_tag": args.run_tag,
        "baseline_version": args.baseline_version,
        "react_version": args.react_version,
        "toolset_version": args.toolset_version,
        "tool_mode": args.tool_mode,
        "dataset_version": args.dataset_version,
        "dataset_source": dataset_source,
        "dataset_size": len(dataset),
        "react_max_steps": args.react_max_steps,
    }
    logger.log_event("BENCHMARK_START", metadata)

    baseline_result = None
    react_result = None
    baseline_scenario = f"baseline:{args.run_tag}:{args.baseline_version}"
    react_scenario = f"react:{args.run_tag}:{args.react_version}"

    if args.mode in ["baseline", "both"]:
        baseline_result = run_baseline(llm, dataset=dataset, scenario=baseline_scenario)
        print_report("Baseline", baseline_result)

    if args.mode in ["react", "both"]:
        react_result = run_react(
            llm,
            dataset=dataset,
            scenario=react_scenario,
            react_max_steps=args.react_max_steps,
            tool_mode=args.tool_mode,
        )
        print_report("ReAct", react_result)

    if baseline_result is not None and react_result is not None:
        comparison = build_comparison(baseline_result, react_result)
        print("\n===== Comparison =====")
        print(f"- baseline avg_keyword_score: {comparison['baseline_avg_keyword_score']}")
        print(f"- react avg_keyword_score: {comparison['react_avg_keyword_score']}")
        print(f"- baseline total_tokens: {comparison['baseline_total_tokens']}")
        print(f"- react total_tokens: {comparison['react_total_tokens']}")
        print(f"- baseline avg_latency_ms: {comparison['baseline_avg_latency_ms']}")
        print(f"- react avg_latency_ms: {comparison['react_avg_latency_ms']}")
        print(f"- react avg_steps: {comparison['react_avg_steps']}")
    elif baseline_result is not None:
        print_single_mode_summary("baseline", baseline_result)
    elif react_result is not None:
        print_single_mode_summary("react", react_result)

    if not args.no_save:
        paths = write_reports(
            output_dir=args.output_dir,
            provider=args.provider,
            model=args.model,
            metadata=metadata,
            baseline_result=baseline_result,
            react_result=react_result,
        )
        print("\n===== Saved Reports =====")
        print(f"- JSON: {paths['json']}")
        print(f"- Markdown: {paths['md']}")
    logger.log_event("BENCHMARK_END", {"mode": args.mode, "run_tag": args.run_tag})


if __name__ == "__main__":
    main()
