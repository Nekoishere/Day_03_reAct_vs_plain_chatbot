# Lab 3: Chatbot vs ReAct Agent (Industry Edition)

Welcome to Phase 3 of the Agentic AI course! This lab focuses on moving from a simple LLM Chatbot to a sophisticated **ReAct Agent** with industry-standard monitoring.

## 🚀 Getting Started

### 1. Setup Environment
Copy the `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Directory Structure
- `src/tools/`: Extension point for your custom tools.

## 🔌 Running with API Providers

This project is configured for hosted API models only.

### OpenAI
```env
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

### Gemini
```env
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-1.5-flash
```

## 🖥️ Running Modes

### CLI
```bash
python main.py
MODE=baseline python main.py
MODE=react python main.py
MODE=compare python main.py
```

### Web UI
```bash
MODE=web python main.py
```

Then open `http://127.0.0.1:8000` in your browser.

## 🎯 Lab Objectives

1.  **Baseline Chatbot**: Observe the limitations of a standard LLM when faced with multi-step reasoning.
2.  **ReAct Loop**: Implement the `Thought-Action-Observation` cycle in `src/agent/agent.py`.
3.  **Provider Switching**: Swap between OpenAI and Gemini seamlessly using the `LLMProvider` interface.
4.  **Failure Analysis**: Use the structured logs in `logs/` to identify why the agent fails (hallucinations, parsing errors).
5.  **Grading & Bonus**: Follow the [SCORING.md](file:///Users/tindt/personal/ai-thuc-chien/day03-lab-agent/SCORING.md) to maximize your points and explore bonus metrics.

## 🛠️ How to Use This Baseline
The code is designed as a **Production Prototype**. It includes:
- **Telemetry**: Every action is logged in JSON format for later analysis.
- **Robust Provider Pattern**: Easily extendable to any LLM API.
- **Clean Skeletons**: Focus on the logic that matters—the agent's reasoning process.

---

*Happy Coding! Let's build agents that actually work.*
