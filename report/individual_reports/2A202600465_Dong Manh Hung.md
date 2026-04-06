# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Dong Manh Hung
- **Student ID**: 2A202600465
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

My main contribution focused on the `agent` and `tools` layers of the project. I worked together with one teammate on these parts, but my own responsibility centered on implementing and refining the ReAct execution loop plus the football tool interface that the agent uses to fetch external information.

- **Modules Implemented**: `src/agent/agent.py`, `src/tools/football_tools.py`
- **Team Collaboration Scope**: I co-developed the Agent + Tools area with one teammate. We shared the same subsystem, but my direct contribution was the ReAct loop behavior, tool calling flow, and argument handling logic.
- **Code Highlights**:
  - Implemented the ReAct loop in `ReActAgent.run()` so the system can iterate through `Thought -> Action -> Observation -> Final Answer`.
  - Implemented action parsing using regex to extract `tool_name(args)` from model output.
  - Implemented `_execute_tool()` to map tool names to Python functions and split arguments according to the tool schema.
  - Worked on the football tool registry in `FOOTBALL_TOOLS`, including tool descriptions, argument schemas, and real-time web search integration.
- **Documentation / Interaction with ReAct Loop**:
  - The `agent` module is the reasoning/controller layer.
  - The `tools` module is the capability layer.
  - The agent decides whether additional information is needed, chooses a tool, calls the tool, receives an observation, and then continues reasoning until it can return a final answer.
  - This design is different from the baseline chatbot, which only sends one direct prompt to the LLM and does not use tools.

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  During testing, the ReAct agent sometimes failed because the LLM did not follow the strict output format. Instead of returning `Thought` and `Action`, it sometimes replied like a normal chatbot. This caused the parser to fail.

- **Log Source**:
  Example from [2026-04-06.log](/home/hung/code/AI_CODE_VIN/lab/testLecssion/lab3/Day_03_reAct_vs_plain_chatbot/logs/2026-04-06.log):

```json
{"timestamp": "2026-04-06T07:06:06.456915", "event": "AGENT_STEP", "data": {"step": 1, "raw_response": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"}}
{"timestamp": "2026-04-06T07:06:06.457578", "event": "AGENT_PARSE_ERROR", "data": {"step": 1, "response": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"}}
```

- **Diagnosis**:
  The root cause was that the model sometimes ignored the strict ReAct format and answered conversationally. In other words, the prompt constraints were not strong enough for all inputs, especially very short or unclear queries. Since the parser in `agent.py` expected a valid `Action:` block, the free-form response could not be executed.

- **Solution**:
  I improved the agent logic in two ways:
  - Strengthened the system prompt to explicitly require the format `Thought -> Action` or `Final Answer`.
  - Added correction behavior in the scratchpad so that when no valid action is found, the model receives feedback and is asked to follow the format strictly on the next step.

  This debugging case showed me that building an agent is not only about creating tools, but also about making the model reliably produce machine-readable outputs.

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   The `Thought` block gives the model a structured intermediate reasoning step before it acts. Compared with the baseline chatbot, this makes the system more suitable for multi-step queries because the agent can explicitly decide whether it needs to use a tool first.

2. **Reliability**:
   The agent did not always perform better. In some simple or malformed inputs, the baseline chatbot was more stable because it only needed to answer normally. The agent could fail when the LLM produced the wrong format, hallucinated a tool name, or gave an invalid action structure.

3. **Observation**:
   Observation is the key difference between direct prompting and agentic behavior. Once the tool returns real data, the next reasoning step becomes grounded in external evidence rather than only in model memory. This usually improved factuality for real-time football questions such as live scores, standings, and lineups.

## IV. Future Improvements (5 Points)

- **Scalability**:
  I would separate tool execution into a more modular service layer and support async execution for cases where multiple external lookups are needed.

- **Safety**:
  I would add stronger validation for tool names and argument formats before execution, plus a fallback guardrail if the model repeatedly outputs invalid actions.

- **Performance**:
  I would improve tool routing and add caching for repeated football queries, especially standings, top scorers, and team form, to reduce latency and API cost.

---

This lab helped me understand that an agent is not just “an LLM with tools.” It is a controlled reasoning loop where tool descriptions, parser robustness, observations, and logs all matter. My contribution on the `agent` and `tools` layers gave me practical experience in how model reasoning can be turned into executable actions.
