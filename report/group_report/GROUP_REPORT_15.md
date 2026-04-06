# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: [GROUP 15 E402]
- **Team Members**: [2A202600141 Nguyễn Công Nhật Tân, 2A202600465-Đồng Mạnh Hùng, 2A202600421-Phan Anh Ly Ly, 2A202600300-Trần Nhật Minh, 2A202600279 - Phan Nguyễn Việt Nhân]
- **Deployment Date**: [06/04/2026]

---

## 1. Executive Summary

*Brief overview of the agent's goal and success rate compared to the baseline chatbot.*

- **Success Rate**: [e.g., 85% on 20 test cases]
- **Key Outcome**: [e.g., "Our agent solved 40% more multi-step queries than the chatbot baseline by correctly utilizing the Search tool."]

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
*Diagram or description of the Thought-Action-Observation loop.*

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `get_live_scores` | `none` | Lấy tỉ số bóng đá trực tiếp của tất cả các giải đấu hiện tại. |
| `get_league_standings`| `string, string` | Lấy bảng xếp hạng của một giải đấu cụ thể trong mùa giải chỉ định. |
| `get_team_results` | `string` | Lấy kết quả 5 trận đấu gần nhất của một đội bóng. |
| `get_match_lineup` | `string` | Lấy đội hình ra sân mới nhất hoặc dự kiến của một đội. |

### 2.3 LLM Providers Used
- **Primary**: GPT-4o-mini  
- **Secondary (Backup)**: Gemini 1.5 Flash (Auto-Fallback khi OpenAI Rate Limited)

---

## 3. Telemetry & Performance Dashboard

*Analyze the industry metrics collected during the final test run.*

- **Average Latency (P50)**: 1942ms
- **Max Latency (P99)**: 7031ms
- **Average Tokens per Task**: 2715 tokens
- **Total Cost of Test Suite**: $0.0073

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*

### Case Study: [e.g., Hallucinated Argument]
- **Input**: "How much is the tax for 500 in Vietnam?"
- **Observation**: Agent called `calc_tax(amount=500, region="Asia")` while the tool only accepts 2-letter country codes.
- **Root Cause**: The system prompt lacked enough `Few-Shot` examples for the tool's strict argument format.

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: [e.g., Adding "Always double check the tool arguments before calling".]
- **Result**: Reduced invalid tool call errors by [e.g., 30%].

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q | Correct | Correct | Draw |
| Multi-step | Hallucinated | Correct | **Agent** |

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Hệ thống có `try...except` bao bọc RateLimit API, xử lý TypeError của Action parse string - chống sập Server.
- **Guardrails**: Bị giới hạn Max `6` vòng loop ngăn Infinite Billing. 
- **Scaling**: Triển khai FastAPI với cơ chế Asynchronous ThreadPool (`def endpoint` thay vì `async def`) phân tán gánh nặng I/O Block giúp Server chạy mượt mà ngay cả khi LLM gọi WebSearch chậm.

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
