import json
from datetime import date
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    ReAct-style agent using OpenAI function calling.
    No regex parsing — the model returns structured tool_calls objects.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        # Pre-build the OpenAI tools schema once
        self._openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in tools
        ]
        # Build a lookup map for fast tool execution
        self._tool_map = {t["name"]: t["func"] for t in tools}

    def _get_system_prompt(self) -> str:
        today = date.today()
        season_start = today.year if today.month >= 8 else today.year - 1
        current_season = f"{season_start}/{season_start + 1}"
        return (
            f"You are a football assistant with access to real-time data tools.\n"
            f"Today's date: {today.isoformat()}. Current season: {current_season}.\n"
            f"Use tools to fetch real data. Only answer from tool results, never guess."
        )

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user",   "content": user_input},
        ]

        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        steps = 0

        while steps < self.max_steps:
            # --- Call LLM with tools ---
            result = self.llm.generate(
                prompt="",           # ignored when messages is provided
                messages=messages,
                tools=self._openai_tools,
            )

            # Accumulate token usage
            for k in total_usage:
                total_usage[k] += result["usage"].get(k, 0)

            tool_calls = result.get("tool_calls")
            content    = result.get("content")

            # --- No tool calls → final answer ---
            if not tool_calls:
                logger.log_event("AGENT_END", {
                    "steps": steps + 1,
                    "answer": content,
                    "total_usage": total_usage,
                })
                return content or "No answer returned."

            # --- Tool calls → execute each, append results ---
            logger.log_event("AGENT_STEP", {
                "step": steps + 1,
                "tool_calls": [tc.function.name for tc in tool_calls],
                "usage": result["usage"],
                "latency_ms": result["latency_ms"],
            })

            # Append the assistant message (contains tool_calls)
            messages.append(result["message"])

            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    kwargs = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    kwargs = {}

                observation = self._execute_tool(tool_name, kwargs)

                logger.log_event("TOOL_CALL", {
                    "tool": tool_name,
                    "args": kwargs,
                    "observation": observation[:300],
                })

                # Append tool result message
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      observation,
                })

            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "reason": "max_steps_reached"})
        return "I ran out of steps to answer your question. Please try rephrasing."

    def _execute_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> str:
        func = self._tool_map.get(tool_name)
        if func is None:
            return f"Tool '{tool_name}' not found. Available: {list(self._tool_map.keys())}"
        try:
            return func(**kwargs)
        except TypeError as e:
            return f"Argument error calling {tool_name}: {e}"
