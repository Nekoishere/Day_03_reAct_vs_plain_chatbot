# API Runbook: Baseline vs ReAct

This runbook is for API-key flow (OpenAI/Gemini). You do not need local GGUF model.

## 1) Project architecture

- `src/chatbot/baseline.py`: direct LLM answer baseline.
- `src/agent/agent.py`: ReAct loop (Thought -> Action -> Observation -> Final Answer).
- `src/tools/football_history.py`: tool registry and local football tools.
- `src/tools/web_research.py`: web research tools (Wikipedia endpoints).
- `src/evaluation/football_eval.py`: eval dataset model and dataset loaders.
- `src/benchmark_football.py`: main benchmark runner + report writer.
- `src/telemetry/metrics.py`: token/latency/cost tracking.
- `src/telemetry/logger.py`: json logs in `logs/`.

## 2) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Use OpenAI:
```env
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY=your_openai_key
```

Or Gemini:
```env
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-1.5-flash
GEMINI_API_KEY=your_gemini_key
```

## 3) Core command patterns

Run both baseline + react:
```bash
python -m src.benchmark_football --mode both --provider openai --model gpt-4o --tool-mode hybrid
```

Run only baseline:
```bash
python -m src.benchmark_football --mode baseline --provider openai --model gpt-4o
```

Run only react:
```bash
python -m src.benchmark_football --mode react --provider openai --model gpt-4o --tool-mode web
```

## 4) Dataset input options

Default dataset (from code):
```bash
python -m src.benchmark_football --mode both
```

Interactive UI input:
```bash
python -m src.benchmark_football --mode both --ui-input
```

CLI questions:
```bash
python -m src.benchmark_football --mode both \
  --question "Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?" \
  --question "Nha vo dich Euro 2016 la ai?" \
  --question "Real Madrid vo dich Champions League cac nam nao trong dataset?"
```

Dataset file:
```bash
python -m src.benchmark_football --mode both --dataset-file ./my_eval.json
```

`my_eval.json` example:
```json
[
  {
    "question": "Ai vo dich World Cup 2018 va ti so chung ket la bao nhieu?",
    "must_have_keywords": ["France", "4-2", "Croatia"]
  },
  {
    "question": "Nha vo dich Euro 2016 la ai?",
    "must_have_keywords": ["Portugal"]
  }
]
```

## 5) Tool modes for ReAct

- `offline`: only local static football tools.
- `web`: only web research tools.
- `hybrid`: web tools + local tools.

Examples:
```bash
python -m src.benchmark_football --mode react --tool-mode offline
python -m src.benchmark_football --mode react --tool-mode web
python -m src.benchmark_football --mode react --tool-mode hybrid
```

## 6) Versioning and debug flags

Use these flags to track experiment versions in logs and reports:

```bash
python -m src.benchmark_football --mode both \
  --run-tag exp_01 \
  --baseline-version baseline_v2 \
  --react-version react_v3 \
  --toolset-version tools_web_v1 \
  --dataset-version userset_v1
```

Useful debug-related flags:
- `--react-max-steps 5`
- `--output-dir report/benchmark_runs`
- `--no-save` (print only, no files)

## 7) Output files

Each run writes:
- `report/benchmark_runs/football_benchmark_<provider>_<run_tag>_<timestamp>.json`
- `report/benchmark_runs/football_benchmark_<provider>_<run_tag>_<timestamp>.md`

The report includes:
- metadata (mode, run_tag, versions, dataset source/size)
- baseline records + metrics
- react records + metrics
- comparison summary (if mode is `both`)

## 8) Recommended lab flow

1. Run `baseline` with a fixed dataset.
2. Run `react` with `tool-mode=web` or `hybrid`.
3. Run `both` with same dataset to compare fairly.
4. Tune prompts/tool descriptions if needed.
5. Re-run with a new `run-tag` to track iteration.

## 9) Troubleshooting

Missing API key:
- Check `.env`.
- Ensure correct provider and model flags.

Low-quality results:
- Make questions explicit.
- Add `must_have_keywords` for objective scoring.
- Use `tool-mode=hybrid` for better robustness.

Local model errors:
- Ignore if you are using OpenAI/Gemini.
- Local model is optional for this API-first workflow.

## 10) Local Web UI

Start local UI:
```bash
./scripts/run_ui.sh
```

Open:
```text
http://127.0.0.1:7860
```

UI endpoint behavior:
- `GET /`: render form
- `POST /api/run`: run pipeline and return JSON result
