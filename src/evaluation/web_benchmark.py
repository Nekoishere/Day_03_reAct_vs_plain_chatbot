import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _sum_usage(events: List[Dict[str, Any]], key: str) -> int:
    total = 0
    for event in events:
        usage = event.get("data", {}).get("usage", {})
        total += int(usage.get(key, 0) or 0)
    return total


def _sum_latency(events: List[Dict[str, Any]], latency_key: str) -> int:
    total = 0
    for event in events:
        total += int(event.get("data", {}).get(latency_key, 0) or 0)
    return total


def build_benchmark_payload(
    question: str,
    baseline_answer: str,
    react_answer: str,
    provider: str,
    model: str,
    log_entries: List[Dict[str, Any]],
) -> Dict[str, Any]:
    generated_at = datetime.utcnow().isoformat()
    baseline_events = [e for e in log_entries if e.get("event") == "CHATBOT_OUTPUT"]
    react_step_events = [e for e in log_entries if e.get("event") == "AGENT_STEP"]
    react_end_events = [e for e in log_entries if e.get("event") == "AGENT_END"]

    baseline_requests = len(baseline_events)
    react_requests = len(react_step_events)

    baseline_metrics = {
        "requests": baseline_requests,
        "total_prompt_tokens": _sum_usage(baseline_events, "prompt_tokens"),
        "total_completion_tokens": _sum_usage(baseline_events, "completion_tokens"),
        "total_tokens": _sum_usage(baseline_events, "total_tokens"),
        "total_latency_ms": _sum_latency(baseline_events, "latency_ms"),
        "avg_latency_ms": round(_sum_latency(baseline_events, "latency_ms") / baseline_requests, 2)
        if baseline_requests else 0.0,
        "total_cost_estimate": round(_sum_usage(baseline_events, "total_tokens") / 1000 * 0.01, 5),
        "avg_keyword_score": None,
    }

    react_steps = []
    for event in react_end_events:
        data = event.get("data", {})
        if "steps" in data:
            react_steps.append(int(data.get("steps", 0) or 0))
        elif "step" in data:
            react_steps.append(int(data.get("step", 0) or 0))

    react_metrics = {
        "requests": react_requests,
        "total_prompt_tokens": _sum_usage(react_step_events, "prompt_tokens"),
        "total_completion_tokens": _sum_usage(react_step_events, "completion_tokens"),
        "total_tokens": _sum_usage(react_step_events, "total_tokens"),
        "total_latency_ms": _sum_latency(react_step_events, "latency_ms"),
        "avg_latency_ms": round(_sum_latency(react_step_events, "latency_ms") / react_requests, 2)
        if react_requests else 0.0,
        "total_cost_estimate": round(_sum_usage(react_step_events, "total_tokens") / 1000 * 0.01, 5),
        "avg_keyword_score": None,
        "avg_steps": round(sum(react_steps) / len(react_steps), 2) if react_steps else 0.0,
    }

    return {
        "generated_at": generated_at,
        "provider": provider,
        "model": model,
        "metadata": {
            "mode": "both",
            "run_tag": "web_compare",
            "baseline_version": "baseline_web_v1",
            "react_version": "react_web_v1",
            "toolset_version": "tools_v1",
            "dataset_version": "web_single_prompt_v1",
            "dataset_source": "web_compare",
            "dataset_size": 1,
            "react_max_steps": 6,
        },
        "baseline": {
            "records": [
                {
                    "question": question,
                    "answer": baseline_answer,
                    "score": None,
                    "method": "baseline",
                }
            ],
            "metrics": baseline_metrics,
        },
        "react": {
            "records": [
                {
                    "question": question,
                    "answer": react_answer,
                    "score": None,
                    "method": "react",
                }
            ],
            "metrics": react_metrics,
        },
        "comparison": {
            "baseline_avg_keyword_score": None,
            "react_avg_keyword_score": None,
            "baseline_total_tokens": baseline_metrics["total_tokens"],
            "react_total_tokens": react_metrics["total_tokens"],
            "baseline_avg_latency_ms": baseline_metrics["avg_latency_ms"],
            "react_avg_latency_ms": react_metrics["avg_latency_ms"],
            "react_avg_steps": react_metrics["avg_steps"],
        },
    }


def _to_markdown(payload: Dict[str, Any]) -> str:
    baseline = payload["baseline"]
    react = payload["react"]
    metadata = payload.get("metadata", {})
    baseline_record = baseline["records"][0]
    react_record = react["records"][0]

    return f"""# Football Benchmark Report

- Generated at: `{payload['generated_at']}`
- Provider: `{payload['provider']}`
- Model: `{payload['model']}`
- Run tag: `{metadata.get('run_tag', '-')}`
- Mode: `{metadata.get('mode', '-')}`
- Dataset source: `{metadata.get('dataset_source', '-')}`
- Dataset size: `{metadata.get('dataset_size', '-')}`
- Baseline version: `{metadata.get('baseline_version', '-')}`
- ReAct version: `{metadata.get('react_version', '-')}`
- Toolset version: `{metadata.get('toolset_version', '-')}`
- Dataset version: `{metadata.get('dataset_version', '-')}`

## Comparison Summary

| Metric | Baseline | ReAct |
|---|---:|---:|
| Avg keyword score | {baseline['metrics']['avg_keyword_score']} | {react['metrics']['avg_keyword_score']} |
| Total tokens | {baseline['metrics']['total_tokens']} | {react['metrics']['total_tokens']} |
| Avg latency (ms) | {baseline['metrics']['avg_latency_ms']} | {react['metrics']['avg_latency_ms']} |
| Avg steps | - | {react['metrics']['avg_steps']} |

## Baseline QA

### Q: {baseline_record['question']}
- Score: `N/A`
- A: {baseline_record['answer']}

## ReAct QA

### Q: {react_record['question']}
- Score: `N/A`
- A: {react_record['answer']}
"""


def save_benchmark_files(payload: Dict[str, Any]) -> Dict[str, str]:
    report_dir = Path("report/benchmark_runs")
    report_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.fromisoformat(payload["generated_at"])
    stamp = generated_at.strftime("%Y%m%d_%H%M%S")
    provider = payload.get("provider", "provider").lower()
    base_name = f"football_benchmark_{provider}_web_compare_{stamp}"

    json_path = report_dir / f"{base_name}.json"
    md_path = report_dir / f"{base_name}.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_to_markdown(payload), encoding="utf-8")

    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
    }
