# Lab 3: Chatbot vs ReAct Agent (API First)

This branch is refactored to benchmark `baseline chatbot` vs `ReAct agent` with OpenAI/Gemini by default.

## Quick start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Prepare env:
```bash
cp .env.example .env
```

3. Put API key in `.env`:
```env
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY=your_key_here
```

4. Run benchmark:
```bash
python -m src.benchmark_football --mode both --provider openai --model gpt-4o --tool-mode hybrid
```

Or use the wrapper script:
```bash
./scripts/run_benchmark.sh --mode both --tool-mode hybrid
```

Script help:
```bash
./scripts/run_benchmark.sh --help-script
```

5. Check output:
- Terminal summary
- `report/benchmark_runs/*.json`
- `report/benchmark_runs/*.md`

## Local Web UI

Start UI:
```bash
./scripts/run_ui.sh
```

Open browser:
```text
http://127.0.0.1:7860
```

In the UI you can:
- select provider/model/mode/tool-mode
- enter football questions (one per line)
- run and view structured JSON result directly

## Full guide

Please use [API_RUNBOOK.md](./API_RUNBOOK.md) for:
- full workflow
- dataset input modes (UI/file/CLI)
- version flags for debug
- tool mode (`offline` / `web` / `hybrid`)
- troubleshooting

## Notes

- Local model (`provider=local`) is optional and not required for normal benchmark flow.
- The recommended flow for this lab is OpenAI/Gemini with API key.
