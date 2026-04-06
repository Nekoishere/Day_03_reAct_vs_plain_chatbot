import time
from typing import Dict, Any, List, Optional, Generator
from openai import OpenAI
from src.core.llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools: Optional[List[Dict[str, Any]]] = None, messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        start_time = time.time()

        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

        kwargs = {"model": self.model_name, "messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        message = response.choices[0].message
        usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }

        return {
            "content": message.content,          # None when tool_calls is present
            "tool_calls": message.tool_calls,    # None when plain text response
            "message": message,                  # full message object for appending to history
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "openai",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except openai.RateLimitError as e:
            from src.core.gemini_provider import GeminiProvider
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                print(f"[OpenAIProvider] RateLimitError! Falling back to GeminiProvider (stream)...")
                gemini = GeminiProvider(api_key=gemini_key)
                yield from gemini.stream(prompt, system_prompt)
            else:
                raise RuntimeError("OpenAI rate limited and no GEMINI_API_KEY available for fallback.") from e
