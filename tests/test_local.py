import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.runtime import build_llm


def test_api_provider_configuration():
    load_dotenv()
    provider_name = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
    provider = build_llm()

    if provider_name == "openai":
        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key
    elif provider_name in ("google", "gemini"):
        assert isinstance(provider, GeminiProvider)
        assert provider.api_key
    else:
        raise AssertionError(f"Unsupported API provider configured: {provider_name}")

    print(f"Configured API provider is valid: {provider_name} ({provider.model_name})")

if __name__ == "__main__":
    test_api_provider_configuration()
