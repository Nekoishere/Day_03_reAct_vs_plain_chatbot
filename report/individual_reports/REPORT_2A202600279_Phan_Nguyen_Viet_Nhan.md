# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phan Nguyen Viet Nhan
- **Student ID**: 2A202600279
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

In this lab, I transitioned the football assistant from a CLI baseline to a high-performance, responsive web application. My main goal was to bridge the gap between "code that works" and "products that users can interact with."

- **Modules Implemented**:
  - `app.py`: The Flask core that serves as the bridge between existing AI logic and the frontend.
  - `src/database.py`: A robust SQLite persistence layer for storing multi-turn conversations and agent reasoning traces.
  - `static/app.js`, `styles.css`, `index.html`: A dark themed UI with effects, dual-mode tabs (Chatbot vs Agent), and reasoning steps.
  - `tests/test_web_app.py`: A full suite of 8 test classes verifying API integrity, DB CRUD, and edge-case handling.

- **Code Highlights**:
  I implemented a non invasive `AgentTracer` in `app.py` to capture thought processes without modifying the core `src/agent/agent.py`. This ensures architectural purity.
  ```python
  # Capturing thought processes for the UI
  if mode == "agent":
      tracer = get_agent_tracer()
      answer, reasoning_steps, latency_ms, usage = tracer.run(user_message, context)
      add_message(conv_id, "assistant", answer, reasoning_trace=reasoning_steps)
  ```

- **Documentation**: My code enables **Follow-up Memory** by rebuilding the conversation context from the SQLite database before every LLM call, allowing the agent to "remember" previous questions in a session.

---

## II. Debugging Case Study (10 Points)

Using the structured logs, I analyzed how the agent handles ambiguity in live data.

- **Problem Description**: Handling query "What is the manchester city current line up?" when no match is currently live.
- **Log Source**: `logs/2026-04-06.log`
- **Diagnosis**: The LLM's initial `Thought` was to "check the latest lineup". The tool `get_match_lineup` returned an observation that "Monday, April 6, 2026... no scheduled match. Their most recent game was on Saturday, April 4... against Liverpool."
- **Solution**: The agent demonstrated high reliability by not "hallucinating" a current lineup. Instead, it transitioned its reasoning to provide the *latest available* data from the April 4th match, clearly stating the context to the user.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The `Thought` block acts as a logical buffer. In the Manchester City case, the agent *decided* to look for a lineup because of its thought process, whereas a pure chatbot would have just guessed based on its 2024 training data.
2.  **Reliability**: The Agent can perform worse if the `Observation` is too verbose or contains irrelevant noise (e.g., search ads), which can occasionally prevent the LLM's focus.
3.  **Observation**: Real world feedback is the core of the agent. Without it, the assistant is just a parrot. The environment's feedback forces the agent to pivot its strategy, moving from a live mindset to a recent history mindset.

---

## IV. Future Improvements (5 Points)

To move this from a lab project to a production-scale sports platform, I propose:

- **AI Score Predictions**: Utilize the existing reasoning trace to feed historical performance data (form, H2H, injuries) into a specialized prediction model to forecast match outcomes.
- **Betting Integration**: Safely integrate a "mock-betting" system allowing users to place stakes based on the agent's insights, creating a more engaging gamified experience.
- **Multi-Sport Expansion**: Generalize the `football_tools.py` into a modular `sports_tools` framework to include Basketball (NBA), Tennis (ATP), and F1.
- **Performance**: Implement a Vector DB (like Pinecone) to retrieve the most relevant tools when the toolset exceeds 50+, reducing the context window usage and cost.

---

> [!NOTE]
> This report documents the successful implementation of a full-stack Agentic AI system that meets all hackathon requirements.
