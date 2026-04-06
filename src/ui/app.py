import json
import os
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

from src.runtime import build_llm, create_baseline_chatbot, create_react_agent


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Football Agent Lab</title>
  <style>
    :root {
      --bg: #f5efe2;
      --panel: rgba(255, 252, 247, 0.9);
      --panel-strong: #fffdf8;
      --text: #1d2433;
      --muted: #596273;
      --line: rgba(29, 36, 51, 0.12);
      --accent: #d85d2a;
      --accent-2: #1d7b6b;
      --accent-3: #2446a8;
      --shadow: 0 22px 50px rgba(64, 40, 18, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(216, 93, 42, 0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(29, 123, 107, 0.18), transparent 26%),
        linear-gradient(135deg, #f6efe2 0%, #f4e4cb 45%, #efe8dd 100%);
      min-height: 100vh;
    }
    .page {
      width: min(1200px, calc(100vw - 32px));
      margin: 24px auto 40px;
      display: grid;
      gap: 18px;
    }
    .hero, .panel {
      background: var(--panel);
      backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      box-shadow: var(--shadow);
      border-radius: 24px;
    }
    .hero {
      padding: 28px;
      position: relative;
      overflow: hidden;
    }
    .hero::after {
      content: "";
      position: absolute;
      inset: auto -80px -80px auto;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(36, 70, 168, 0.22), transparent 70%);
    }
    h1 {
      margin: 0 0 8px;
      font-size: clamp(2rem, 4vw, 3.4rem);
      line-height: 0.95;
      letter-spacing: -0.03em;
    }
    .lead {
      margin: 0;
      max-width: 70ch;
      color: var(--muted);
      font-size: 1.03rem;
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
    .grid {
      display: grid;
      grid-template-columns: 1.35fr 0.95fr;
      gap: 18px;
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
      color: var(--text);
    }
    textarea {
      min-height: 136px;
      resize: vertical;
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
    .primary { background: var(--accent); color: white; }
    .secondary { background: var(--accent-2); color: white; }
    .ghost { background: rgba(255,255,255,0.7); color: var(--text); border: 1px solid var(--line); }
    .stack {
      display: grid;
      gap: 14px;
    }
    .answer {
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.72);
      white-space: pre-wrap;
      line-height: 1.55;
      min-height: 108px;
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
    .logs {
      min-height: 420px;
      max-height: 640px;
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
    @media (max-width: 960px) {
      .grid, .compare { grid-template-columns: 1fr; }
      .page { width: min(100vw - 20px, 1200px); }
      .hero, .panel { border-radius: 20px; }
    }
  </style>
</head>
<body>
  <main class="page">
    <section class="hero">
      <h1>Football Agent Lab</h1>
      <p class="lead">A web front-end for comparing a plain football chatbot against a ReAct agent that can decide when to call live-data tools.</p>
      <div class="meta">
        <div class="pill" id="provider-pill">Provider: loading...</div>
        <div class="pill" id="model-pill">Model: loading...</div>
        <div class="pill">Modes: baseline, react, compare</div>
      </div>
    </section>

    <section class="grid">
      <div class="stack">
        <section class="panel">
          <h2>Prompt Console</h2>
          <label for="mode">Mode</label>
          <select id="mode">
            <option value="react">ReAct Agent</option>
            <option value="baseline">Baseline Chatbot</option>
            <option value="compare">Compare Both</option>
          </select>

          <label for="message" style="margin-top: 14px;">Question</label>
          <textarea id="message" placeholder="Ask about live scores, standings, lineups, form, injuries, or any football query you want to test."></textarea>

          <div class="actions">
            <button class="primary" id="send-btn">Run Query</button>
            <button class="secondary" id="reset-btn">Reset Baseline Memory</button>
            <button class="ghost" id="logs-btn">Refresh Logs</button>
          </div>
          <div class="hint">Use compare mode to see how the two systems behave on the exact same input.</div>
          <div class="status" id="status"></div>
        </section>

        <section class="panel">
          <h2>Response</h2>
          <div id="single-answer" class="answer">No response yet.</div>
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
        </section>
      </div>

      <section class="panel">
        <h2>Recent Logs</h2>
        <div id="logs" class="logs">Loading logs...</div>
      </section>
    </section>
  </main>

  <script>
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
      logs: document.getElementById("logs")
    };

    function setBusy(isBusy, label = "Working...") {
      els.sendBtn.disabled = isBusy;
      els.resetBtn.disabled = isBusy;
      if (isBusy) {
        els.status.textContent = label;
      }
    }

    function renderSingleAnswer(text) {
      els.compareAnswer.hidden = true;
      els.singleAnswer.hidden = false;
      els.singleAnswer.textContent = text || "No response returned.";
    }

    function renderCompareAnswer(payload) {
      els.singleAnswer.hidden = true;
      els.compareAnswer.hidden = false;
      els.baselineAnswer.textContent = payload.baseline || "No baseline response returned.";
      els.reactAnswer.textContent = payload.react || "No agent response returned.";
    }

    async function loadStatus() {
      const response = await fetch("/api/status");
      const data = await response.json();
      els.providerPill.textContent = `Provider: ${data.provider}`;
      els.modelPill.textContent = `Model: ${data.model}`;
    }

    async function loadLogs() {
      const response = await fetch("/api/logs?lines=40");
      const data = await response.json();
      els.logs.textContent = data.logs || "No logs yet.";
    }

    async function runQuery() {
      const message = els.message.value.trim();
      if (!message) {
        els.status.textContent = "Please enter a question first.";
        return;
      }

      const mode = els.mode.value;
      setBusy(true, `Running ${mode}...`);

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

        if (mode === "compare") {
          renderCompareAnswer(data);
        } else {
          renderSingleAnswer(data.answer);
        }

        els.status.textContent = `Completed at ${new Date(data.timestamp).toLocaleTimeString()}`;
        await loadLogs();
      } catch (error) {
        els.status.textContent = error.message;
      } finally {
        setBusy(false, els.status.textContent);
      }
    }

    async function resetBaseline() {
      setBusy(true, "Resetting baseline memory...");
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
            return {
                "baseline": self.baseline.chat(message),
                "react": self.react.run(message),
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
        return "No log file has been created yet."

    with log_path.open("r", encoding="utf-8") as handle:
        content = handle.readlines()
    return "".join(content[-lines:]).strip() or "Log file is empty."


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
            self._send_json({"logs": _read_recent_logs(line_count)})
            return

        self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/chat":
            payload = self._read_json_body()
            mode = str(payload.get("mode", "react")).strip().lower()
            message = str(payload.get("message", "")).strip()

            if not message:
                self._send_json({"error": "Message must not be empty."}, status=HTTPStatus.BAD_REQUEST)
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
            self._send_json({"message": "Baseline history and agent state were reset."})
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
