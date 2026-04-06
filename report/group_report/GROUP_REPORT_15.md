# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: GROUP 15 E402
- **Team Members**: 2A202600141-Nguyễn Công Nhật Tân, 2A202600465-Đồng Mạnh Hùng, 2A202600421-Phan Anh Ly Ly, 2A202600300-Trần Nhật Minh, 2A202600279-Phan Nguyễn Việt Nhân
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

This project compares a baseline football chatbot against a ReAct agent that can use tools for real-time and multi-step football queries.  
The evaluation focuses on answer quality, tool-use correctness, context retention, and graceful handling of out-of-domain questions.

- **Success Rate**: Chatbot 4/5, Agent 5/5 (on 5 core test cases)
- **Key Outcome**: The agent outperformed the chatbot on real-time and multi-step tasks by grounding responses in tool observations and preserving reasoning trace; however, this comparison is not fully symmetric because the baseline chatbot is limited by training cutoff while the agent can access fresh tool data.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
The agent follows a strict `Thought -> Action -> Observation` cycle and repeats this loop until it has enough evidence to produce `Final Answer`.  
Each step is logged and exposed to the UI as `reasoning_trace` for transparency and RCA.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_live_scores` | `none` | Lấy tỉ số bóng đá trực tiếp của tất cả các giải đấu hiện tại. |
| `get_league_standings` | `league_name, season` | Lấy bảng xếp hạng của một giải đấu cụ thể trong mùa giải chỉ định. |
| `get_top_scorers` | `league_name, season` | Lấy danh sách vua phá lưới theo giải đấu và mùa giải. |
| `get_team_form` | `team_name` | Lấy phong độ 5 trận gần nhất của đội bóng. |
| `get_player_stats` | `player_name, season` | Lấy thống kê cầu thủ theo mùa giải. |
| `get_injury_report` | `team_name` | Lấy thông tin chấn thương/cầu thủ vắng mặt mới nhất. |
| `get_head_to_head` | `team1, team2` | So sánh lịch sử đối đầu giữa hai đội. |
| `get_match_lineup` | `team_name` | Lấy đội hình ra sân mới nhất hoặc dự kiến của một đội. |

### 2.3 LLM Providers Used
- **Primary**: GPT-4o-mini (OpenAI)
- **Secondary (Backup)**: Gemini 1.5 Flash (fallback when needed)

---

## 3. Telemetry & Performance Dashboard

Analyze the industry metrics collected during the final test run.

- **Average Latency (P50)**: 1942ms
- **Max Latency (P99)**: 7031ms
- **Average Tokens per Task**: 2715 tokens
- **Total Cost of Test Suite**: $0.0073

### 3.1 Final Test Suite (5 Required Cases)
| Case ID | Test Purpose | Input | Expected Chatbot Behavior | Expected Agent Behavior | Pass Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC1 | Simple factual football question | "What are the current Premier League standings?" | Provides a reasonable non-tool answer | Provides correct answer (with or without tool) | Answer relevant and coherent |
| TC2 | Multi-step football reasoning | "Compare Arsenal vs Chelsea head-to-head and summarize who has better recent form." | May be generic or partially hallucinated | Uses tools and synthesizes a comparative summary | Correct comparison grounded in observations |
| TC3 | Real-time football request | "What are the live football scores right now?" | Clearly states no real-time access | Calls live score tool and returns current data | No hallucination; response reflects real-time/tool output |
| TC4 | Out-of-domain handling | "Can you explain quantum computing in simple terms?" | Graceful refusal/redirection to football | Graceful refusal/redirection to football | No crash, no 500 error, polite response |
| TC5 | Follow-up context retention | Turn 1: "Tell me about Liverpool this season." Turn 2: "What about their injuries now?" | May lose context between turns | Keeps context and answers follow-up correctly | Follow-up uses prior context correctly |

### 3.2 Final Run Results (Observed)
| Case ID | Chatbot | Agent | Notes |
| :--- | :--- | :--- | :--- |
| TC1 | Pass | Pass | Both answered correctly. |
| TC2 | Partial Fail | Pass | Chatbot generic; agent used multi-step evidence. |
| TC3 | Pass | Pass | Chatbot refused real-time correctly; agent returned tool-grounded live info. |
| TC4 | Pass | Pass | Both handled out-of-domain politely without crashing. |
| TC5 | Fail | Pass | Chatbot lost context in follow-up; agent retained context and tool flow. |

---

## 4. Root Cause Analysis (RCA) - Failure Traces

Deep dive into why the agent failed.

### Case Study: Multi-step comparison inconsistency (early iteration, TC2)
- **Input**: "Compare Arsenal vs Chelsea head-to-head and summarize who has better recent form."
- **Observation**: In earlier prompt version, the agent retrieved partial data, then concluded before gathering complete comparison evidence.
- **Root Cause**: Prompt instructions were not strict enough on evidence completeness before generating final output.
- **Mitigation**: Added explicit guardrail: "Do not produce Final Answer until both sides have comparable observations."
- **Post-fix Result**: TC2 improved from partial/unstable to consistent pass in final run.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: Added explicit checks: "Validate tool arguments, and do not finalize until all required observations are collected."
- **Result**: Invalid tool-call/early-finalization issues reduced by ~25%; multi-step consistency improved.

### Experiment 2 (Bonus): Chatbot vs Agent
**Fairness note**: Baseline chatbot answers only from pretrained knowledge (time-limited), while the agent can query real-time tools.  
Therefore, "winner" for live-data tasks should be interpreted as capability difference (static model vs tool-augmented system), not purely model quality.

| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| TC1 - Simple Q | Correct | Correct | Draw |
| TC2 - Multi-step | Generic / incomplete reasoning | Correct, tool-grounded | **Agent** |
| TC3 - Real-time | Correctly refuses due to no live access | Correct live data via tools | **Agent** (tool advantage) |
| TC4 - Out-of-domain | Graceful redirect | Graceful redirect | Draw |
| TC5 - Follow-up context | Lost context | Correct context retention | **Agent** |

---

## 6. Production Readiness Review

Considerations for taking this system to a real-world environment.

- **Security**: Enforce strict input validation/sanitization for tool arguments and API payloads; rate-limit external tool calls.
- **Guardrails**: Keep bounded reasoning loops (`max_steps=6`) to prevent infinite cost and fail safely on malformed actions.
- **Scaling**: Add caching for repeated tool results and async queue execution for slow tool calls to improve concurrency.

---

