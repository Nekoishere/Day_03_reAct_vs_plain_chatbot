# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phan Anh Ly Ly
- **Student ID**: 2A202600421
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

### Modules Implemented
| Module | Description |
|---|---|
| `src/tools/football_tools.py` | Built and refined football tools (live scores, standings, player/team stats, injuries, fixtures, H2H, facts) using OpenAI `web_search_preview`. |
| `src/agent/agent.py` | Implemented ReAct loop with OpenAI function-calling, bounded `max_steps`, tool execution, and persistent turn history. |
| `src/core/openai_provider.py` | Added unified `generate()` interface supporting both plain prompts and tool-calling messages. |
| `app.py` | Integrated web app routes for chatbot/agent modes, reasoning trace response, latency/token usage, and conversation auto-title. |
| `tests/test_web_app.py` | Added and validated API/database test coverage, including non-football query handling. |

### Code Highlights
- Implemented strict separation between baseline chatbot and tool-augmented agent to enable fair side-by-side evaluation.
- Exposed reasoning transparency in web mode via `reasoning_trace`, allowing users to inspect agent steps.
- Improved freshness of tool outputs in `football_tools.py` by forcing up-to-date web search phrasing in the query.

## II. Debugging Case Study (10 Points)

**Problem Description**:  
In early runs, the agent sometimes returned stale football facts (for example, answers anchored to older seasons) even when a tool call was expected to fetch fresh information.

**Log Source**:  
Telemetry events from `TOOL_CALL` and final response flow (`AGENT_STEP` -> `TOOL_CALL` -> `AGENT_END`) showed that tool usage happened, but observations were not always clearly "latest" in content.

**Diagnosis**:  
`web_search_preview` can behave inconsistently when the query is too generic. If the prompt looks like a static fact question, the response may drift toward prior knowledge style wording instead of strongly time-anchored results.

**Solution**:  
I adjusted tool query construction in `_web_search()` (`src/tools/football_tools.py`) by appending an explicit freshness instruction:  
`search the web for the latest up-to-date information, do not rely on training data`.  
After this change, live/current-season tasks (scores, standings, injuries) became more consistent in agent mode.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:  
The ReAct agent outperforms the baseline on multi-step queries (e.g., Form + Injuries + H2H) by dynamically calling tools and synthesizing observations rather than relying on a single-pass response from static training data.

2. **Reliability**:  
The agent is superior for complex tasks but carries higher latency and cost. Its reliability is strictly coupled to tool performance; if tool outputs are noisy or incomplete, the agent may propagate those errors into the final response.

3. **Observation**:  
Concrete observations are the primary defense against hallucination. This project confirms that while the ReAct loop provides the framework for accuracy, the final output quality is ultimately limited by the precision and currency of the underlying data tools.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Move tool execution to async workers/queue (Celery or task queue) and cache repeated football queries to reduce duplicated web calls.
- **Safety**: Add output guardrails for unsupported/out-of-domain prompts and add stricter schema validation before executing tool arguments.
- **Performance**: Route only top-k relevant tools per query (instead of exposing all tools each turn) to reduce token overhead and improve latency.

---

