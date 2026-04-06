# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Tran Nhat Minh
- **Student ID**: 2A202600300
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

### Modules Implemented

| Module | Description |
|---|---|
| `src/tools/football_tools.py` | 13 football data tools backed by OpenAI `web_search_preview` |
| `src/chatbot/chatbot.py` | Baseline chatbot with conversation memory using OpenAI messages format |
| `src/agent/agent.py` | Full ReAct agent using OpenAI function calling (no regex) |
| `src/core/openai_provider.py` | Extended `generate()` to accept `tools` and `messages` params |
| `main.py` | Entry point supporting `baseline`, `react`, and `compare` modes |

### Code Highlights

**1. OpenAI Function Calling in `agent.py`**

Replaced the fragile regex-based `Action: tool_name(args)` parsing with native OpenAI function calling. The agent now receives structured `tool_calls` objects:

**2. Forcing web search in `football_tools.py`**

Discovered that `web_search_preview` is optional — the model skips it and answers from training data if the query seems like general knowledge. Fixed by appending an explicit instruction:

```python
response = _get_client().responses.create(
    model="gpt-4o-mini",
    tools=[{"type": "web_search_preview"}],
    input=f"{query} (search the web for the latest up-to-date information, do not rely on training data)",
)
```

**3. Conversation memory in `agent.py`**

Each `run()` call now persists the full turn (user message, tool call messages, assistant response) into `self.history`, which is prepended to the next call's messages list:

```python
messages = (
    [{"role": "system", "content": self._get_system_prompt()}]
    + self.history          # previous turns
    + [new_user_msg]        # current question
)
# After answer:
self.history.extend(turn_messages)
```
`
## II. Debugging Case Study (10 Points)

### Web search not activated, stale training data returned

**Problem Description:**
When asking *"How many times has Vietnam won the AFF Cup?"*, the `search_football_facts` tool was called but the observation said *"As of 2023, Vietnam has won the AFF Cup twice"* — the correct answer is three times (2008, 2018, 2024).

**Log Source** (`logs/2026-04-06.log`):
```json
{
  "event": "TOOL_CALL",
  "data": {
    "tool": "search_football_facts",
    "args": { "query": "How many times has Vietnam won the AFF Cup" },
    "observation": "As of 2023, Vietnam has won the AFF Cup twice, in 2008 and 2018."
  }
}
```

**Diagnosis:**
`web_search_preview` is an **optional** tool — OpenAI's model decides whether to actually perform a web search or answer from training data. For a query that looks like general knowledge (*"how many times has X won Y"*), the model skipped the live search and answered from its 2023 training cutoff, which predates Vietnam's 2024 AFF Cup victory.

**Solution:**`
Appended a forcing instruction to every query inside `_web_search()`:

```python
input=f"{query} (search the web for the latest up-to-date information, do not rely on training data)"
```

After the fix, the same query returned:
```
As of April 2026, Vietnam has won the AFF Championship three times: in 2008, 2018, and 2024.
```

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning: How did tool-based reasoning help?

The baseline chatbot answers questions in a single forward pass — whatever GPT-4o knows from training data comes out immediately. This is fast but fundamentally limited to static knowledge with a hard cutoff date (October 2023 in our case).

The ReAct agent, by contrast, decomposes the question before answering. When asked *"Who are the top 3 scorers in the Premier League right now?"*, the agent first reasoned: *"I need live data for the current 2025/2026 season"*, then called `get_top_scorers(Premier League, 2025/2026)`, received real web data, and only then formulated the answer. The `Thought` step acts as a planning phase that routes the question to the right tool with the right parameters.

This is especially visible in multi-step questions like *"Should I start Salah in my fantasy team?"* — the agent chains `get_player_stats` → `get_next_fixture` → `get_injury_report` into a coherent reasoning trace that a single-shot chatbot cannot replicate.

### 2. Reliability: When did the agent perform worse?

The agent underperformed the chatbot in three situations observed during the lab:

**a) Query reformulation losing context:**
When the user asked *"Việt Nam vô địch AFF Cup vào năm 2008, 2018 và 2024 đúng không?"* (confirming the 2024 win), the agent reformulated the query to a generic *"Việt Nam vô địch AFF Cup năm nào"* — dropping the year anchors — and received stale data that contradicted the user's own correct statement. The chatbot, while unable to confirm the 2024 win, at least didn't actively contradict the user.

**b) No memory across turns (before the fix):**
Each `agent.run()` call started fresh. After correctly finding the 2024 AFF Cup win in turn 1, the agent had no recollection in turn 2 and re-searched, sometimes getting different (stale) results. The chatbot's simpler history mechanism was more consistent within a session.

**c) Cost and latency:**
Every agent response involves at minimum 2 LLM calls (one to decide the tool, one to synthesize the answer) plus one `web_search_preview` call. The baseline chatbot answers in a single call at ~100 tokens. For simple factual questions within training data (e.g., *"What formation does a 4-3-3 use?"*), the chatbot is faster, cheaper, and equally accurate.

### 3. Observation: How did feedback influence the agent?

The observation after each tool call acts as grounding — it prevents the LLM from drifting into hallucination. Two concrete examples:

**Positive grounding:** After receiving *"Erling Haaland (Manchester City) — 22 goals"* as an observation, the agent's Final Answer referenced exactly that number. Without the observation, a pure chatbot would have cited Haaland's previous season goals as if they were current.

**Negative grounding (stale observation):** When the web search tool returned *"As of 2023..."*, the agent dutifully reported that stale data as fact. This shows observations are trusted unconditionally — the agent has no built-in skepticism about the quality of tool results. This is a key architectural weakness: garbage in, garbage out. The fix (forcing the web search) addressed the root cause in the tool layer rather than the agent layer.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Replace sequential tool calls with parallel execution using `asyncio`. When a question requires multiple independent tools (e.g., stats for two teams), both can be called simultaneously, halving latency.
- **Safety**: Add a Critic LLM pass after each Final Answer that checks whether the answer actually came from tool observations and not from training data. Flag and retry if the answer contains phrases like *"as of my knowledge"* or *"I believe"*.
- **Performance**: For a system with many tools (50+), use vector similarity search over tool descriptions to select the top-k relevant tools per query rather than passing all tools to every LLM call, reducing prompt token cost significantly.
