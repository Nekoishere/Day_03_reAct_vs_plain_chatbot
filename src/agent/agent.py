import re
from datetime import date
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    """
    A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Tools internally use OpenAI web search to fetch real-time football data.
    """

    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 6):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
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

    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})

        scratchpad = f"Question: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            # 1. Generate next Thought + Action (or Final Answer)
            result = self.llm.generate(scratchpad, system_prompt=self.get_system_prompt())
            llm_output = result["content"].strip()

            logger.log_event("AGENT_STEP", {
                "step": steps + 1,
                "llm_output": llm_output,
                "usage": result["usage"],
                "latency_ms": result["latency_ms"],
            })

            # 2. Check for Action first (takes priority)
            action_match = re.search(r"Action:\s*(\w+)\(([^)]*)\)", llm_output)

            if not action_match:
                # No Action — look for Final Answer
                if "Final Answer:" in llm_output:
                    final = llm_output.split("Final Answer:")[-1].strip()
                    logger.log_event("AGENT_END", {"steps": steps + 1, "answer": final})
                    return final
                # Neither — prompt correction
                scratchpad += llm_output + "\nObservation: No valid Action found. Follow the format strictly.\n"
                steps += 1
                continue

            tool_name = action_match.group(1).strip()
            raw_args = action_match.group(2).strip()

            # 3. Execute tool
            observation = self._execute_tool(tool_name, raw_args)

            logger.log_event("TOOL_CALL", {
                "tool": tool_name,
                "args": raw_args,
                "observation": observation[:300],  # truncate for log
            })

            # 4. Append observation to scratchpad and continue
            scratchpad += llm_output + f"\nObservation: {observation}\n"
            steps += 1

        logger.log_event("AGENT_END", {"steps": steps, "reason": "max_steps_reached"})
        return "I ran out of steps to answer your question. Please try rephrasing."

    def _execute_tool(self, tool_name: str, raw_args: str) -> str:
        """
        Find the tool, parse arguments, and call it.
        Splits on the last comma when schema has 2 args to handle
        multi-word first args like 'Premier League, 2025'.
        """
        for tool in self.tools:
            if tool["name"] == tool_name:
                func = tool["func"]
                schema = tool.get("args_schema", [])

                if not schema:
                    return func()

                # Smart split: if 2 args expected, split on last comma only
                if len(schema) == 2 and "," in raw_args:
                    last_comma = raw_args.rfind(",")
                    raw_parts = [raw_args[:last_comma].strip(), raw_args[last_comma + 1:].strip()]
                else:
                    raw_parts = [a.strip() for a in raw_args.split(",") if a.strip()]

                # Cast to int where possible
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

        return f"Tool '{tool_name}' not found. Available: {[t['name'] for t in self.tools]}"
