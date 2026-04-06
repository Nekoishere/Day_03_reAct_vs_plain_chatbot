import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class ReActAgent:
    """
    SKELETON: A ReAct-style Agent that follows the Thought-Action-Observation loop.
    Students should implement the core loop logic and tool execution.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.history = []

    def get_system_prompt(self) -> str:
        """
        TODO: Implement the system prompt that instructs the agent to follow ReAct.
        Should include:
        1.  Available tools and their descriptions.
        2.  Format instructions: Thought, Action, Observation.
        """
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}" for t in self.tools])
        return f"""
        You are an intelligent assistant. You have access to the following tools:
        {tool_descriptions}

        Use the following format:
        Thought: your line of reasoning.
        Action: tool_name(arguments)
        Observation: result of the tool call.
        ... (repeat Thought/Action/Observation if needed)
        Final Answer: your final response.
        """

    def run(self, user_input: str) -> str:
        """
        TODO: Implement the ReAct loop logic.
        1. Generate Thought + Action.
        2. Parse Action and execute Tool.
        3. Append Observation to prompt and repeat until Final Answer.
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        self.history = []
        steps = 0
        final_answer = None

        while steps < self.max_steps:
            current_prompt = self._build_prompt(user_input)
            result = self.llm.generate(current_prompt, system_prompt=self.get_system_prompt())
            content = result.get("content", "").strip()

            tracker.track_request(
                provider=result.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=result.get("usage", {}),
                latency_ms=result.get("latency_ms", 0),
                scenario="react",
            )

            logger.log_event(
                "AGENT_STEP",
                {
                    "step": steps + 1,
                    "raw_response": content,
                },
            )

            answer_match = re.search(r"Final\s*Answer\s*:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
            if answer_match:
                final_answer = answer_match.group(1).strip()
                break

            action = self._parse_action(content)
            if action is None:
                logger.log_event(
                    "AGENT_PARSE_ERROR",
                    {"step": steps + 1, "response": content},
                )
                final_answer = content
                break

            tool_name, args = action
            observation = self._execute_tool(tool_name, args)
            self.history.append(
                {
                    "thought_action": content,
                    "observation": observation,
                }
            )
            steps += 1

        if final_answer is None:
            final_answer = "Tôi đã đạt giới hạn số bước và chưa thể kết luận chắc chắn."

        logger.log_event("AGENT_END", {"steps": steps, "final_answer": final_answer})
        return final_answer

    def _build_prompt(self, user_input: str) -> str:
        if not self.history:
            return user_input

        transcript = []
        for i, step in enumerate(self.history, start=1):
            transcript.append(f"Step {i}:\n{step['thought_action']}\nObservation: {step['observation']}")
        return f"User question: {user_input}\n\nPrevious steps:\n" + "\n\n".join(transcript)

    def _parse_action(self, content: str) -> Optional[tuple]:
        match = re.search(r"Action\s*:\s*([a-zA-Z_]\w*)\((.*)\)", content, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        tool_name = match.group(1).strip()
        args = match.group(2).strip()
        if args.startswith('"') and args.endswith('"'):
            args = args[1:-1]
        if args.startswith("'") and args.endswith("'"):
            args = args[1:-1]
        return tool_name, args

    def _execute_tool(self, tool_name: str, args: str) -> str:
        """
        Helper method to execute tools by name.
        """
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    return str(tool["func"](args))
                except Exception as exc:
                    logger.log_event("TOOL_EXECUTION_ERROR", {"tool": tool_name, "error": str(exc)})
                    return f"Tool {tool_name} failed: {exc}"
        return f"Tool {tool_name} not found."
