import os
import traceback
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from src.benchmark_football import build_comparison, create_provider, run_baseline, run_react
from src.evaluation.football_eval import FOOTBALL_DATASET, EvalSample, build_dataset_from_questions
from src.telemetry.metrics import tracker


load_dotenv()

app = Flask(__name__, template_folder="templates")


def _non_empty_lines(text: str) -> List[str]:
    return [line.strip() for line in (text or "").splitlines() if line.strip()]


def _resolve_dataset(questions_text: str) -> List[EvalSample]:
    lines = _non_empty_lines(questions_text)
    if not lines:
        return FOOTBALL_DATASET
    return build_dataset_from_questions(lines)


def _resolve_api_key(provider: str) -> str:
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY", "")
    if provider == "google":
        return os.getenv("GEMINI_API_KEY", "")
    return ""


def _run_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    provider = payload.get("provider", os.getenv("DEFAULT_PROVIDER", "openai"))
    model = payload.get("model", os.getenv("DEFAULT_MODEL", "gpt-4o"))
    mode = payload.get("mode", "both")
    tool_mode = payload.get("tool_mode", "hybrid")
    run_tag = payload.get("run_tag", "ui")
    baseline_version = payload.get("baseline_version", "baseline_ui_v1")
    react_version = payload.get("react_version", "react_ui_v1")
    dataset_version = payload.get("dataset_version", "dataset_ui_v1")
    toolset_version = payload.get("toolset_version", "tools_ui_v1")
    react_max_steps = int(payload.get("react_max_steps", 5))
    questions_text = payload.get("questions", "")

    dataset = _resolve_dataset(questions_text)
    api_key = _resolve_api_key(provider)
    llm = create_provider(provider_name=provider, model_name=model, api_key=api_key)
    tracker.reset()

    baseline_result: Optional[Dict[str, Any]] = None
    react_result: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None

    baseline_scenario = f"baseline:{run_tag}:{baseline_version}"
    react_scenario = f"react:{run_tag}:{react_version}"

    if mode in ["baseline", "both"]:
        baseline_result = run_baseline(llm=llm, dataset=dataset, scenario=baseline_scenario)

    if mode in ["react", "both"]:
        react_result = run_react(
            llm=llm,
            dataset=dataset,
            scenario=react_scenario,
            react_max_steps=react_max_steps,
            tool_mode=tool_mode,
        )

    if baseline_result is not None and react_result is not None:
        comparison = build_comparison(baseline_result, react_result)

    return {
        "metadata": {
            "provider": provider,
            "model": model,
            "mode": mode,
            "tool_mode": tool_mode,
            "run_tag": run_tag,
            "baseline_version": baseline_version,
            "react_version": react_version,
            "dataset_version": dataset_version,
            "toolset_version": toolset_version,
            "dataset_size": len(dataset),
            "react_max_steps": react_max_steps,
        },
        "baseline": baseline_result,
        "react": react_result,
        "comparison": comparison,
    }


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        default_provider=os.getenv("DEFAULT_PROVIDER", "openai"),
        default_model=os.getenv("DEFAULT_MODEL", "gpt-4o"),
    )


@app.route("/api/run", methods=["POST"])
def run_benchmark_api():
    try:
        payload = request.get_json(silent=True) or {}
        result = _run_pipeline(payload)
        return jsonify({"ok": True, "result": result})
    except Exception as exc:
        return jsonify(
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        ), 500


def main():
    host = os.getenv("UI_HOST", "127.0.0.1")
    port = int(os.getenv("UI_PORT", "7860"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
