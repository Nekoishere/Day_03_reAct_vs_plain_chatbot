# Lab 3: Chatbot vs ReAct Agent

A football statistics assistant comparing a plain LLM chatbot against a ReAct agent with real-time tool access.

## Setup

### 1. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your API key and preferred provider:

```env
# Choose one: openai | google
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o-mini

OPENAI_API_KEY=your_key_here   # if using openai
GEMINI_API_KEY=your_key_here   # if using google
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the App

### Web UI (recommended)

Starts a Flask server with a browser-based chat interface:

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser. The UI lets you switch between **Chatbot** and **ReAct Agent** modes and shows the agent's reasoning trace.

### CLI

Run interactively in the terminal. Set `MODE` in `.env` or pass it inline:

**Baseline chatbot** (no real-time data):
```bash
MODE=baseline python main.py
```

**ReAct agent** (uses football tools):
```bash
MODE=react python main.py
```

**Side-by-side comparison** (runs both on a fixed set of queries):
```bash
MODE=compare python main.py
```

Type `exit` or `quit` to stop the CLI session.

## Project Structure

```
app.py              # Flask web app entry point
main.py             # CLI entry point
src/
  agent/            # ReAct agent implementation
  chatbot/          # Baseline chatbot implementation
  core/             # LLM provider wrappers (OpenAI, Gemini)
  tools/            # Football data tools used by the agent
  telemetry/        # JSON structured logging
  database.py       # SQLite conversation storage
static/             # Frontend (HTML/CSS/JS)
logs/               # Per-day JSON logs
```

## Using a Local Model (CPU)

To run without an API key using a local GGUF model:

1. Download [Phi-3-mini-4k-instruct-q4.gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf) (~2.2 GB)
2. Place it in a `models/` folder at the project root
3. Update `.env`:

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

> Note: The web app (`app.py`) does not support the `local` provider. Use `main.py` for local model inference.
