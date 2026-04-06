import json
import os
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from src.evaluation.web_benchmark import build_benchmark_payload, save_benchmark_files
from src.runtime import build_llm, create_baseline_chatbot, create_react_agent
from src.telemetry.logger import logger


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Football Agent Lab</title>
  <style>
    :root {
      --paper: #f4efe6;
      --panel: rgba(255, 250, 241, 0.88);
      --panel-strong: #fffdf8;
      --ink: #1b2230;
      --muted: #5e6875;
      --line: rgba(27, 34, 48, 0.12);
      --orange: #d66a31;
      --green: #19725f;
      --blue: #1d4c8f;
      --gold: #d4a73a;
      --shadow: 0 24px 60px rgba(35, 29, 18, 0.14);
      --radius: 26px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214, 106, 49, 0.18), transparent 26%),
        radial-gradient(circle at 85% 10%, rgba(25, 114, 95, 0.18), transparent 20%),
        radial-gradient(circle at 55% 90%, rgba(29, 76, 143, 0.14), transparent 22%),
        linear-gradient(135deg, #f6eee0 0%, #f0e4cf 44%, #ebe5dd 100%);
      min-height: 100vh;
    }
    .page {
      width: min(1280px, calc(100vw - 28px));
      margin: 20px auto 36px;
      display: grid;
      gap: 16px;
    }
    .hero, .panel {
      background: var(--panel);
      backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
    }
    .hero {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }
    .hero::before,
    .hero::after {
      content: "";
      position: absolute;
      border-radius: 50%;
      pointer-events: none;
    }
    .hero::before {
      inset: -120px auto auto -60px;
      width: 260px;
      height: 260px;
      background: radial-gradient(circle, rgba(214, 106, 49, 0.18), transparent 68%);
    }
    .hero::after {
      inset: auto -80px -80px auto;
      width: 280px;
      height: 280px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(29, 76, 143, 0.18), transparent 70%);
    }
    .hero-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: 1.25fr 0.9fr;
      gap: 16px;
      align-items: end;
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2.2rem, 4vw, 3.8rem);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }
    .lead {
      margin: 0;
      max-width: 64ch;
      color: var(--muted);
      font-size: 1.04rem;
    }
    .meta {
      margin-top: 18px;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 8px 12px;
      font-size: 0.92rem;
      background: rgba(255, 255, 255, 0.7);
    }
    .hero-note {
      padding: 18px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.55)),
        linear-gradient(135deg, rgba(214, 106, 49, 0.08), rgba(25, 114, 95, 0.12));
      border: 1px solid rgba(255, 255, 255, 0.45);
    }
    .hero-note strong {
      display: block;
      margin-bottom: 8px;
      font-size: 0.82rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .hero-note p {
      margin: 0;
      color: var(--muted);
      line-height: 1.55;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.95fr);
      gap: 16px;
    }
    .panel {
      padding: 20px;
    }
    .panel h2 {
      margin: 0 0 12px;
      font-size: 1.15rem;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    .panel-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 0.9rem;
      color: var(--muted);
    }
    select, textarea, button {
      font: inherit;
    }
    select, textarea {
      width: 100%;
      border-radius: 18px;
      border: 1px solid var(--line);
      padding: 14px 16px;
      background: var(--panel-strong);
      color: var(--ink);
    }
    textarea {
      min-height: 132px;
      resize: vertical;
    }
    .control-grid {
      display: grid;
      grid-template-columns: 220px minmax(0, 1fr);
      gap: 14px;
      align-items: end;
      margin-bottom: 12px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      cursor: pointer;
      transition: transform 120ms ease, opacity 120ms ease;
    }
    button:hover { transform: translateY(-1px); }
    button:disabled { opacity: 0.6; cursor: wait; transform: none; }
    .primary { background: var(--orange); color: white; }
    .secondary { background: var(--green); color: white; }
    .ghost { background: rgba(255,255,255,0.7); color: var(--ink); border: 1px solid var(--line); }
    .stack {
      display: grid;
      gap: 14px;
    }
    .story-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(260px, 0.85fr);
      gap: 14px;
    }
    .answer {
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
      white-space: pre-wrap;
      line-height: 1.55;
      min-height: 180px;
    }
    .answer strong {
      color: var(--ink);
    }
    .compare {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    .card {
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
      border-radius: 18px;
      padding: 14px;
    }
    .card h3 {
      margin: 0 0 8px;
      font-size: 1rem;
    }
    .status {
      font-size: 0.92rem;
      color: var(--muted);
      min-height: 22px;
    }
    .samples {
      display: grid;
      gap: 8px;
    }
    .sample-btn {
      width: 100%;
      text-align: left;
      border-radius: 16px;
      border: 1px solid var(--line);
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.76);
      color: var(--ink);
    }
    .sample-btn small {
      display: block;
      color: var(--muted);
      margin-top: 4px;
      font-size: 0.8rem;
    }
    .mini-stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }
    .stat {
      border-radius: 18px;
      padding: 14px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.66);
    }
    .stat strong {
      display: block;
      font-size: 1.4rem;
      margin-bottom: 4px;
    }
    .stat span {
      color: var(--muted);
      font-size: 0.88rem;
    }
    .timeline {
      display: grid;
      gap: 10px;
      max-height: 420px;
      overflow: auto;
      padding-right: 4px;
    }
    .event {
      position: relative;
      padding: 14px 14px 14px 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.7);
    }
    .event::before {
      content: "";
      position: absolute;
      inset: 14px auto 14px 0;
      width: 4px;
      border-radius: 999px;
      background: var(--gold);
    }
    .event[data-kind="AGENT_STEP"]::before,
    .event[data-kind="TOOL_CALL"]::before { background: var(--orange); }
    .event[data-kind="CHATBOT_OUTPUT"]::before { background: var(--green); }
    .event[data-kind="AGENT_END"]::before { background: var(--blue); }
    .event time {
      display: block;
      color: var(--muted);
      font-size: 0.8rem;
      margin-bottom: 6px;
    }
    .event strong {
      display: block;
      margin-bottom: 6px;
      font-size: 0.88rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .event pre {
      margin: 0;
      white-space: pre-wrap;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 0.82rem;
      line-height: 1.45;
      color: var(--ink);
    }
    .logs {
      min-height: 250px;
      max-height: 320px;
      overflow: auto;
      padding: 16px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: #1a1f29;
      color: #f2f2ea;
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 0.86rem;
      line-height: 1.45;
    }
    .hint {
      margin-top: 10px;
      color: var(--muted);
      font-size: 0.92rem;
    }
    .muted {
      color: var(--muted);
      font-size: 0.9rem;
    }
    @media (max-width: 960px) {
      .hero-grid, .grid, .compare, .story-grid, .mini-stats, .control-grid { grid-template-columns: 1fr; }
      .page { width: min(100vw - 20px, 1200px); }
      .hero, .panel { border-radius: 20px; }
    }
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero-grid">
        <div>
          <h1>Football Agent Studio</h1>
          <p class="lead">So sánh chatbot bóng đá cơ bản với ReAct agent có thể tự chọn tool, lấy dữ liệu web mới và trả lời dựa trên quan sát thật.</p>
          <div class="meta">
            <div class="pill" id="provider-pill">Provider: đang tải...</div>
            <div class="pill" id="model-pill">Model: đang tải...</div>
            <div class="pill" id="timestamp-pill">Phiên: đang tải...</div>
          </div>
        </div>
        <div class="hero-note">
          <strong>Cách Đọc Lab Này</strong>
          <p>`Baseline` trả lời từ trí nhớ của model. `ReAct` tự quyết định khi nào cần thêm dữ liệu, gọi tool bóng đá, nhận observation rồi mới trả lời. `Compare` chạy cả hai trên cùng một câu hỏi để thấy khác biệt rõ ràng.</p>
        </div>
      </div>
    </section>

    <section class="grid">
      <div class="stack">
        <section class="panel">
          <div class="panel-head">
            <h2>Bảng Điều Khiển Prompt</h2>
            <div class="muted">Ctrl/Cmd + Enter để chạy</div>
          </div>
          <div class="control-grid">
            <div>
              <label for="mode">Chế độ</label>
              <select id="mode">
                <option value="react">ReAct Agent</option>
                <option value="baseline">Chatbot Cơ Bản</option>
                <option value="compare">So Sánh Cả Hai</option>
              </select>
            </div>
            <div>
              <label for="message">Câu hỏi</label>
              <textarea id="message" placeholder="Hỏi về tỉ số trực tiếp, bảng xếp hạng, đội hình, phong độ, chấn thương, hoặc bất kỳ câu hỏi bóng đá nào bạn muốn test."></textarea>
            </div>
          </div>

          <div class="actions">
            <button class="primary" id="send-btn">Chạy Truy Vấn</button>
            <button class="secondary" id="reset-btn">Đặt Lại Bộ Nhớ Baseline</button>
            <button class="ghost" id="logs-btn">Làm Mới Log</button>
          </div>
          <div class="hint">Dùng chế độ so sánh khi bạn muốn thấy rõ nhất vì sao tools và suy luận nhiều bước lại quan trọng.</div>
          <div class="status" id="status"></div>
        </section>

        <section class="panel">
          <div class="panel-head">
            <h2>Kết Quả</h2>
            <div class="muted" id="result-meta">Chưa có lượt chạy nào.</div>
          </div>
          <div class="story-grid">
            <div>
              <div id="single-answer" class="answer">Hãy chạy một prompt để xem kết quả mới nhất ở đây.</div>
              <div id="compare-answer" class="compare" hidden>
                <div class="card">
                  <h3>Baseline</h3>
                  <div id="baseline-answer" class="answer"></div>
                </div>
                <div class="card">
                  <h3>ReAct Agent</h3>
                  <div id="react-answer" class="answer"></div>
                </div>
              </div>
            </div>
            <div class="stack">
              <div class="mini-stats">
                <div class="stat">
                  <strong id="run-mode-stat">-</strong>
                  <span>Chế độ gần nhất</span>
                </div>
                <div class="stat">
                  <strong id="history-stat">0</strong>
                  <span>Số prompt trong phiên</span>
                </div>
                <div class="stat">
                  <strong id="events-stat">0</strong>
                  <span>Sự kiện trace hiển thị</span>
                </div>
              </div>
              <div>
                <div class="panel-head">
                  <h2 style="margin:0;">Prompt Nhanh</h2>
                  <div class="muted">Bấm để nạp</div>
                </div>
                <div class="samples">
                  <button class="sample-btn" data-prompt="What are the live football scores right now?">Tỉ Số Trực Tiếp<small>Phù hợp để thấy ranh giới giữa model và tool rất nhanh.</small></button>
                  <button class="sample-btn" data-prompt="Who are the top 3 scorers in the Premier League this season?">Top Ghi Bàn Premier League<small>Rất hợp để chạy chế độ so sánh.</small></button>
                  <button class="sample-btn" data-prompt="What is the lineup for Real Madrid today?">Đội Hình Real Madrid<small>Kiểm tra dữ liệu bóng đá gần thời gian thực.</small></button>
                  <button class="sample-btn" data-prompt="Show me the recent results for Manchester United.">Phong Độ Gần Đây<small>Cho thấy câu trả lời được grounding qua tool.</small></button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <div class="stack">
        <section class="panel">
          <div class="panel-head">
            <h2>Trace Gần Đây</h2>
            <div class="muted">Các sự kiện có cấu trúc mới nhất</div>
          </div>
          <div id="timeline" class="timeline">
            <div class="event">
              <strong>Đang Chờ</strong>
              <pre>Hãy chạy một prompt, các sự kiện telemetry mới nhất sẽ hiện ở đây.</pre>
            </div>
          </div>
        </section>
        <section class="panel">
          <div class="panel-head">
            <h2>Log Thô</h2>
            <div class="muted">40 dòng gần nhất</div>
          </div>
          <div id="logs" class="logs">Đang tải log...</div>
        </section>
      </div>
    </section>
  </main>

  <script>
    const sessionHistory = [];
    const els = {
      mode: document.getElementById("mode"),
      message: document.getElementById("message"),
      sendBtn: document.getElementById("send-btn"),
      resetBtn: document.getElementById("reset-btn"),
      logsBtn: document.getElementById("logs-btn"),
      status: document.getElementById("status"),
      singleAnswer: document.getElementById("single-answer"),
      compareAnswer: document.getElementById("compare-answer"),
      baselineAnswer: document.getElementById("baseline-answer"),
      reactAnswer: document.getElementById("react-answer"),
      providerPill: document.getElementById("provider-pill"),
      modelPill: document.getElementById("model-pill"),
      timestampPill: document.getElementById("timestamp-pill"),
      logs: document.getElementById("logs"),
      timeline: document.getElementById("timeline"),
      resultMeta: document.getElementById("result-meta"),
      runModeStat: document.getElementById("run-mode-stat"),
      historyStat: document.getElementById("history-stat"),
      eventsStat: document.getElementById("events-stat")
    };

    function setBusy(isBusy, label = "Đang xử lý...") {
      els.sendBtn.disabled = isBusy;
      els.resetBtn.disabled = isBusy;
      if (isBusy) {
        els.status.textContent = label;
      }
    }

    function renderSingleAnswer(text) {
      els.compareAnswer.hidden = true;
      els.singleAnswer.hidden = false;
      els.singleAnswer.textContent = text || "Không có phản hồi nào được trả về.";
    }

    function renderCompareAnswer(payload) {
      els.singleAnswer.hidden = true;
      els.compareAnswer.hidden = false;
      els.baselineAnswer.textContent = payload.baseline || "Baseline không trả về phản hồi.";
      els.reactAnswer.textContent = payload.react || "Agent không trả về phản hồi.";
    }

    function formatEvent(entry) {
      if (!entry || !entry.event) return "Không có payload sự kiện.";
      const data = entry.data || {};
      if (entry.event === "AGENT_STEP") {
        return data.llm_output || data.raw_response || JSON.stringify(data, null, 2);
      }
      if (entry.event === "TOOL_CALL") {
        return `Tool: ${data.tool || "-"}\\nArgs: ${data.args || "-"}\\nObservation: ${data.observation || "-"}`;
      }
      if (entry.event === "CHATBOT_OUTPUT") {
        return data.output || JSON.stringify(data, null, 2);
      }
      if (entry.event === "AGENT_START" || entry.event === "CHATBOT_INPUT") {
        return data.input || JSON.stringify(data, null, 2);
      }
      if (entry.event === "AGENT_END") {
        return data.answer || data.final_answer || JSON.stringify(data, null, 2);
      }
      return JSON.stringify(data, null, 2);
    }

    function renderTimeline(entries) {
      if (!entries.length) {
        els.timeline.innerHTML = `<div class="event"><strong>Đang Chờ</strong><pre>Hãy chạy một prompt, các sự kiện telemetry mới nhất sẽ hiện ở đây.</pre></div>`;
        els.eventsStat.textContent = "0";
        return;
      }

      els.timeline.innerHTML = entries.map((entry) => {
        const timestamp = entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : "Không rõ thời gian";
        const body = formatEvent(entry)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;");
        return `<article class="event" data-kind="${entry.event}">
          <time>${timestamp}</time>
          <strong>${entry.event}</strong>
          <pre>${body}</pre>
        </article>`;
      }).join("");
      els.eventsStat.textContent = String(entries.length);
    }

    function updateSessionMeta(mode, timestamp, summary = "") {
      sessionHistory.push({ mode, timestamp });
      els.runModeStat.textContent = mode;
      els.historyStat.textContent = String(sessionHistory.length);
      els.resultMeta.textContent = summary || `Lượt chạy gần nhất lúc ${new Date(timestamp).toLocaleTimeString()}`;
    }

    async function loadStatus() {
      const response = await fetch("/api/status");
      const data = await response.json();
      els.providerPill.textContent = `Provider: ${data.provider}`;
      els.modelPill.textContent = `Model: ${data.model}`;
      els.timestampPill.textContent = `Phiên: ${new Date(data.timestamp).toLocaleTimeString()}`;
    }

    async function loadLogs() {
      const response = await fetch("/api/logs?lines=40");
      const data = await response.json();
      els.logs.textContent = data.logs || "Chưa có log nào.";
      renderTimeline(data.entries || []);
    }

    async function runQuery() {
      const message = els.message.value.trim();
      if (!message) {
        els.status.textContent = "Hãy nhập câu hỏi trước.";
        return;
      }

      const mode = els.mode.value;
      setBusy(true, `Đang chạy ${mode}...`);

      try {
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode, message })
        });
        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.error || "Request failed");
        }

        let resultSummary = "";
        if (mode === "compare") {
          renderCompareAnswer(data);
          if (data.benchmark) {
            resultSummary = `Đã lưu benchmark | JSON: ${data.benchmark.json_path.split("/").pop()} | MD: ${data.benchmark.md_path.split("/").pop()}`;
          }
        } else {
          renderSingleAnswer(data.answer);
        }

        updateSessionMeta(mode, data.timestamp, resultSummary);
        els.status.textContent = `Hoàn tất lúc ${new Date(data.timestamp).toLocaleTimeString()}`;
        await loadLogs();
      } catch (error) {
        els.status.textContent = error.message;
      } finally {
        setBusy(false, els.status.textContent);
      }
    }

    async function resetBaseline() {
      setBusy(true, "Đang đặt lại bộ nhớ baseline...");
      try {
        const response = await fetch("/api/reset", { method: "POST" });
        const data = await response.json();
        els.status.textContent = data.message;
      } catch (error) {
        els.status.textContent = error.message;
      } finally {
        setBusy(false, els.status.textContent);
      }
    }

    els.sendBtn.addEventListener("click", runQuery);
    els.resetBtn.addEventListener("click", resetBaseline);
    els.logsBtn.addEventListener("click", loadLogs);
    els.message.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        runQuery();
      }
    });
    document.querySelectorAll(".sample-btn").forEach((button) => {
      button.addEventListener("click", () => {
        els.message.value = button.dataset.prompt || "";
        els.message.focus();
      });
    });

    loadStatus();
    loadLogs();
  </script>
</body>
</html>
"""


class AppState:
    def __init__(self):
        self.llm = build_llm()
        self.baseline = create_baseline_chatbot(self.llm)
        self.react = create_react_agent(self.llm, max_steps=6)

    def reset(self):
        self.baseline.reset()
        self.react = create_react_agent(self.llm, max_steps=6)

    def run_chat(self, mode: str, message: str) -> Dict[str, Any]:
        if mode == "baseline":
            return {"answer": self.baseline.chat(message)}

        if mode == "react":
            return {"answer": self.react.run(message)}

        if mode == "compare":
            summary = self.provider_summary()
            start_line = _log_line_count()

            logger.log_event("BENCHMARK_START", {
                "mode": "both",
                "run_tag": "web_compare",
                "dataset_source": "web_compare",
                "dataset_size": 1,
                "react_max_steps": 6,
            })

            baseline_answer = self.baseline.chat(message)
            react_answer = self.react.run(message)
            log_entries = _read_log_entries_from(start_line)

            benchmark_payload = build_benchmark_payload(
                question=message,
                baseline_answer=baseline_answer,
                react_answer=react_answer,
                provider=summary["provider"],
                model=summary["model"],
                log_entries=log_entries,
            )
            benchmark_paths = save_benchmark_files(benchmark_payload)

            logger.log_event("BENCHMARK_END", {
                "mode": "both",
                "run_tag": "web_compare",
                "dataset_source": "web_compare",
                "json_path": benchmark_paths["json_path"],
                "md_path": benchmark_paths["md_path"],
            })

            return {
                "baseline": baseline_answer,
                "react": react_answer,
                "benchmark": benchmark_paths,
            }

        raise ValueError(f"Unsupported mode: {mode}")

    def provider_summary(self) -> Dict[str, str]:
        provider_name = getattr(self.llm, "__class__", type(self.llm)).__name__
        return {"provider": provider_name, "model": self.llm.model_name}


STATE = AppState()


def _log_path() -> Path:
    return Path("logs") / f"{datetime.now().strftime('%Y-%m-%d')}.log"


def _read_recent_logs(lines: int = 40) -> str:
    log_path = _log_path()
    if not log_path.exists():
        return "Chưa có file log nào được tạo."

    with log_path.open("r", encoding="utf-8") as handle:
        content = handle.readlines()
    return "".join(content[-lines:]).strip() or "File log đang trống."


def _log_line_count() -> int:
    log_path = _log_path()
    if not log_path.exists():
        return 0

    with log_path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def _read_log_entries_from(start_line: int) -> list[Dict[str, Any]]:
    log_path = _log_path()
    if not log_path.exists():
        return []

    with log_path.open("r", encoding="utf-8") as handle:
        raw_lines = handle.readlines()[start_line:]

    entries = []
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        entries.append(payload)
    return entries


def _read_recent_log_entries(lines: int = 12) -> list[Dict[str, Any]]:
    log_path = _log_path()
    if not log_path.exists():
        return []

    with log_path.open("r", encoding="utf-8") as handle:
        raw_lines = handle.readlines()[-lines:]

    entries = []
    for raw in raw_lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        entries.append(payload)
    return entries


class FootballLabHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(HTML_PAGE)
            return

        if parsed.path == "/api/status":
            payload = STATE.provider_summary()
            payload["timestamp"] = datetime.utcnow().isoformat()
            self._send_json(payload)
            return

        if parsed.path == "/api/logs":
            params = parse_qs(parsed.query)
            raw_lines = params.get("lines", ["40"])[0]
            try:
                line_count = max(1, min(200, int(raw_lines)))
            except ValueError:
                line_count = 40
            self._send_json({
                "logs": _read_recent_logs(line_count),
                "entries": _read_recent_log_entries(min(12, line_count)),
            })
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/chat":
            payload = self._read_json_body()
            mode = str(payload.get("mode", "react")).strip().lower()
            message = str(payload.get("message", "")).strip()

            if not message:
                self._send_json({"error": "Câu hỏi không được để trống."}, status=HTTPStatus.BAD_REQUEST)
                return

            try:
                result = STATE.run_chat(mode, message)
                result["timestamp"] = datetime.utcnow().isoformat()
                self._send_json(result)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        if parsed.path == "/api/reset":
            STATE.reset()
            self._send_json({"message": "Đã đặt lại lịch sử baseline và trạng thái agent."})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        return json.loads(raw or "{}")

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data: Dict[str, Any], status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = None, port: int = None):
    host = host or os.getenv("WEB_HOST", "127.0.0.1")
    port = int(port or os.getenv("WEB_PORT", "8000"))

    server = ThreadingHTTPServer((host, port), FootballLabHandler)
    print(f"Web UI running at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server()
