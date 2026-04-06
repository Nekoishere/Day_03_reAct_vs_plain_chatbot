# Roadmap Du An: So Sanh Baseline Chatbot vs ReAct

## 1) Muc tieu
- Xay dung 2 che do tra loi:
  - Baseline chatbot: tra loi truc tiep bang LLM.
  - ReAct agent: Thought -> Action -> Observation -> Final Answer.
- Do metric de so sanh:
  - `avg_keyword_score`
  - `total_tokens`
  - `avg_latency_ms`
  - `avg_steps` (chi cho ReAct)
- Xuat bao cao tu dong ra `JSON` va `Markdown`.

## 2) Cau truc chinh
- `src/chatbot/baseline.py`: logic chatbot baseline.
- `src/agent/agent.py`: ReAct loop + goi tools.
- `src/tools/football_history.py`: tools va dataset lich su bong da.
- `src/evaluation/football_eval.py`: tap cau hoi test + ham cham diem.
- `src/benchmark_football.py`: entrypoint chay benchmark va xuat report.

## 3) Chuan bi moi truong
```bash
pip install -r requirements.txt
cp .env.example .env
```

## 4) Cau hinh provider
### OpenAI
```env
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY=...
```

### Gemini
```env
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-1.5-flash
GEMINI_API_KEY=...
```

### Local
```env
DEFAULT_PROVIDER=local
DEFAULT_MODEL=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

## 5) Chay benchmark
```bash
python -m src.benchmark_football --provider openai --model gpt-4o
```

Tuy chon:
```bash
python -m src.benchmark_football --provider google --model gemini-1.5-flash
python -m src.benchmark_football --provider local --model local
```

## 6) File output
Mac dinh script se luu:
- `report/benchmark_runs/football_benchmark_<provider>_<timestamp>.json`
- `report/benchmark_runs/football_benchmark_<provider>_<timestamp>.md`

Neu chi muon in console:
```bash
python -m src.benchmark_football --provider openai --model gpt-4o --no-save
```

## 7) Cach doc ket qua
- Neu `react_avg_keyword_score` > `baseline_avg_keyword_score`: ReAct cho ket qua dung hon.
- Neu `react_total_tokens` cao hon baseline: chi phi cao hon do co nhieu vong suy luan.
- `react_avg_steps` cho thay do sau lap (qua cao => can toi uu prompt/tool).

## 8) Vong lap cai tien de nop lab
1. Chay benchmark lan 1.
2. Phan tich log trong `logs/`.
3. Tinh chinh system prompt/tool descriptions.
4. Chay lai benchmark lan 2.
5. So sanh 2 file report markdown va rut ra ket luan.
