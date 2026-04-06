"""
Flask Web Application for Football Statistics Agent & Chatbot.
Serves the UI and provides REST API endpoints.
"""
import os
import re
import time
import json
from datetime import date
from typing import List, Dict, Any, Optional

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.chatbot.chatbot import BaselineChatbot
from src.agent.agent import ReActAgent
from src.tools.football_tools import FOOTBALL_TOOLS
from src.database import (
    init_db, create_conversation, get_conversations, get_conversation,
    delete_conversation, update_conversation_title, add_message,
    get_messages, get_conversation_context
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder="static", static_url_path="/static")

# ---------------------------------------------------------------------------
# LLM / Agent / Chatbot singletons
# ---------------------------------------------------------------------------
def build_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    if provider == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "google":
        return GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    else:
        raise ValueError(f"Unknown provider: {provider}")

llm = None
chatbot_instance = None
agent_instance = None

def get_llm():
    global llm
    if llm is None:
        llm = build_llm()
    return llm

def get_chatbot():
    global chatbot_instance
    if chatbot_instance is None:
        chatbot_instance = BaselineChatbot(get_llm())
    return chatbot_instance

def get_agent():
    global agent_instance
    if agent_instance is None:
        agent_instance = ReActAgent(get_llm(), tools=FOOTBALL_TOOLS, max_steps=6)
    return agent_instance


# ---------------------------------------------------------------------------
# Agent wrapper — captures reasoning trace without modifying agent.py
# ---------------------------------------------------------------------------
class AgentTracer:
    """
    Runs the ReAct agent while capturing step-by-step reasoning for the UI.
    Re-implements the loop logic to capture traces — the original agent.py
    is NOT modified.
    """

    def __init__(self, llm, tools, max_steps=6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def _get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )
        today = date.today()
        season_start = today.year if today.month >= 8 else today.year - 1
        current_season = f"{season_start}/{season_start + 1}"

        return f"""You are a football assistant agent with access to real-time data tools.
Today's date: {today.isoformat()}. The current football season is {current_season}.
When a tool requires a season argument, always use the format YYYY/YYYY (e.g. {current_season}) unless the user specifies otherwise.

Available tools:
{tool_descriptions}

You MUST follow this strict format for every step:

Thought: <your reasoning about what to do next>
Action: <tool_name>(<arg1>, <arg2>, ...)

Then STOP. Do NOT write Observation yourself — it will be filled in automatically.
After receiving an Observation, continue with another Thought/Action or end with:

Final Answer: <your complete answer to the user>

Rules:
- Only use tools listed above.
- Write argument values directly — no quotes, no variable names.
- Never write Observation: yourself.
- Only write Final Answer after you have received real Observation data.
- Never combine Action and Final Answer in the same response.
"""

    def _execute_tool(self, tool_name: str, raw_args: str) -> str:
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool["func"]
                schema = tool.get("args_schema", [])
                if not schema:
                    return func()
                n = len(schema)
                if n > 1 and "," in raw_args:
                    raw_parts = [p.strip() for p in raw_args.rsplit(",", n - 1)]
                else:
                    raw_parts = [raw_args.strip()] if raw_args.strip() else []
                parsed_args = []
                for part in raw_parts:
                    try:
                        parsed_args.append(int(part))
                    except ValueError:
                        parsed_args.append(part)
                try:
                    return func(*parsed_args)
                except TypeError as e:
                    return f"Argument error calling {tool_name}: {e}"
        return f"Tool '{tool_name}' not found."

    def run(self, user_input: str, context: str = ""):
        """
        Run the agent and return (answer, reasoning_steps, total_latency_ms, total_usage).
        reasoning_steps is a list of dicts: {type, content, tool?, args?, observation?}
        """
        prompt = context + f"User: {user_input}\n" if context else f"Question: {user_input}\n"
        scratchpad = prompt
        steps = 0
        reasoning_steps = []
        total_latency = 0
        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        while steps < self.max_steps:
            result = self.llm.generate(scratchpad, system_prompt=self._get_system_prompt())
            llm_output = result["content"].strip()
            latency = result.get("latency_ms", 0)
            usage = result.get("usage", {})

            total_latency += latency
            for k in total_usage:
                total_usage[k] += usage.get(k, 0)

            action_match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", llm_output)

            if not action_match:
                if "Final Answer:" in llm_output:
                    final = llm_output.split("Final Answer:")[-1].strip()
                    # Extract thought if present
                    thought_match = re.search(r"Thought:\s*(.*?)(?=Final Answer:)", llm_output, re.DOTALL)
                    if thought_match:
                        reasoning_steps.append({
                            "type": "thought",
                            "content": thought_match.group(1).strip()
                        })
                    reasoning_steps.append({
                        "type": "final_answer",
                        "content": final
                    })
                    return final, reasoning_steps, total_latency, total_usage

                reasoning_steps.append({
                    "type": "error",
                    "content": "No valid Action found. Retrying..."
                })
                scratchpad += llm_output + "\nObservation: No valid Action found. Follow the format strictly.\n"
                steps += 1
                continue

            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()

            # Extract thought
            thought_match = re.search(r"Thought:\s*(.*?)(?=Action:)", llm_output, re.DOTALL)
            thought_text = thought_match.group(1).strip() if thought_match else ""

            observation = self._execute_tool(tool_name, raw_args)

            reasoning_steps.append({
                "type": "step",
                "thought": thought_text,
                "tool": tool_name,
                "args": raw_args,
                "observation": observation[:500]  # Truncate for UI
            })

            scratchpad += llm_output + f"\nObservation: {observation}\n"
            steps += 1

        return "I ran out of steps. Please try rephrasing.", reasoning_steps, total_latency, total_usage


# Global tracer
agent_tracer = None

def get_agent_tracer():
    global agent_tracer
    if agent_tracer is None:
        agent_tracer = AgentTracer(get_llm(), FOOTBALL_TOOLS, max_steps=6)
    return agent_tracer


# ---------------------------------------------------------------------------
# Suggested questions
# ---------------------------------------------------------------------------
SUGGESTED_QUESTIONS = [
    "What are the live football scores right now?",
    "Who are the top scorers in the Premier League this season?",
    "What are the current Premier League standings?",
    "Show me the recent results for Manchester United.",
    "What is the lineup for Real Madrid today?",
    "Compare the head-to-head record of Arsenal vs Chelsea.",
    "What are Mohamed Salah's stats this season?",
    "Who is injured at Liverpool right now?",
    "When is Barcelona's next match?",
    "What was the result of Manchester City vs Liverpool?",
]


# ---------------------------------------------------------------------------
# Routes — Static
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.route("/api/model-info", methods=["GET"])
def model_info():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    return jsonify({"provider": provider, "model": model})


@app.route("/api/suggestions", methods=["GET"])
def suggestions():
    return jsonify({"suggestions": SUGGESTED_QUESTIONS})


@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    convos = get_conversations()
    return jsonify({"conversations": convos})


@app.route("/api/conversations", methods=["POST"])
def create_new_conversation():
    data = request.get_json()
    mode = data.get("mode", "chatbot")
    model_name = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    title = data.get("title", "New Conversation")
    conv_id = create_conversation(mode, model_name, title)
    conv = get_conversation(conv_id)
    return jsonify({"conversation": conv}), 201


@app.route("/api/conversations/<int:conv_id>", methods=["DELETE"])
def delete_conv(conv_id):
    success = delete_conversation(conv_id)
    if success:
        return jsonify({"status": "deleted"}), 200
    return jsonify({"error": "Not found"}), 404


@app.route("/api/conversations/<int:conv_id>/messages", methods=["GET"])
def list_messages(conv_id):
    msgs = get_messages(conv_id)
    return jsonify({"messages": msgs})


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Body: { conversation_id, message, mode }
    Returns: { reply, reasoning_trace?, latency_ms, usage }
    """
    data = request.get_json()
    conv_id = data.get("conversation_id")
    user_message = data.get("message", "").strip()
    mode = data.get("mode", "chatbot")

    if not conv_id or not user_message:
        return jsonify({"error": "conversation_id and message are required"}), 400

    # Check conversation exists
    conv = get_conversation(conv_id)
    if not conv:
        return jsonify({"error": "Conversation not found"}), 404

    # Save user message
    add_message(conv_id, "user", user_message)

    # Build context from conversation history for follow-up support
    context = get_conversation_context(conv_id)

    try:
        if mode == "agent":
            tracer = get_agent_tracer()
            answer, reasoning_steps, latency_ms, usage = tracer.run(user_message, context)

            add_message(
                conv_id, "assistant", answer,
                reasoning_trace=reasoning_steps,
                latency_ms=latency_ms,
                token_usage=usage
            )

            # Auto-title: use first user message (truncated)
            if len(get_messages(conv_id)) <= 2:
                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                update_conversation_title(conv_id, title)

            return jsonify({
                "reply": answer,
                "reasoning_trace": reasoning_steps,
                "latency_ms": latency_ms,
                "usage": usage
            })

        else:  # chatbot mode
            # Use the chatbot but with conversation context
            bot = get_chatbot()
            # Reset internal history and inject our DB context
            bot.history = []
            db_messages = get_messages(conv_id)
            for msg in db_messages:
                if msg["role"] == "user":
                    # Find the next assistant message
                    pass
            # Rebuild history pairs from DB
            pairs = []
            i = 0
            while i < len(db_messages) - 1:
                if db_messages[i]["role"] == "user" and i + 1 < len(db_messages) and db_messages[i + 1]["role"] == "assistant":
                    pairs.append({"user": db_messages[i]["content"], "assistant": db_messages[i + 1]["content"]})
                    i += 2
                else:
                    i += 1
            bot.history = pairs[-6:]  # Keep last 6 turns

            start = time.time()
            result = bot.llm.generate(
                context + f"User: {user_message}",
                system_prompt="You are a knowledgeable football assistant. Answer questions about football matches, scores, teams, players, and statistics. Important: You rely only on your training data — you do NOT have access to real-time or live information. If asked about live scores or very recent events, clearly say you don't have access to real-time data."
            )
            latency_ms = int((time.time() - start) * 1000)
            answer = result["content"]
            usage = result.get("usage", {})

            add_message(
                conv_id, "assistant", answer,
                latency_ms=latency_ms,
                token_usage=usage
            )

            # Update chatbot's internal history too
            bot.history.append({"user": user_message, "assistant": answer})

            # Auto-title
            if len(get_messages(conv_id)) <= 2:
                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                update_conversation_title(conv_id, title)

            return jsonify({
                "reply": answer,
                "reasoning_trace": None,
                "latency_ms": latency_ms,
                "usage": usage
            })

    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        add_message(conv_id, "assistant", error_msg)
        return jsonify({"error": error_msg}), 500


# ---------------------------------------------------------------------------
# Init & Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("\n" + "=" * 60)
    print("  ⚽ Football Statistics Agent & Chatbot")
    print(f"  Model: {os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')}")
    print(f"  Provider: {os.getenv('DEFAULT_PROVIDER', 'openai')}")
    print("  URL: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
