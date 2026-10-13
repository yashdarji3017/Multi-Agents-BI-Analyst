"""Base utilities, Microsoft Agent Framework Gemini client initialization, and native Gemini token counting."""

import logging
import os
from typing import Any, Optional, Tuple
from businessinsight.config import settings

logger = logging.getLogger(__name__)


try:
    from agent_framework import Agent
    from agent_framework.gemini import GeminiChatClient
    MAF_AVAILABLE = True
except ImportError:
    Agent = None
    GeminiChatClient = None
    MAF_AVAILABLE = False


def is_maf_gemini_ready() -> bool:
    """Checks if Microsoft Agent Framework is installed and Gemini credentials are configured."""
    api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    return MAF_AVAILABLE and bool(api_key)


def get_gemini_agent(name: str, instructions: str) -> Optional[Any]:
    """Initializes a Microsoft Agent Framework Agent powered by GeminiChatClient.

    Returns the Agent instance, or None if dependencies or credentials are unavailable.
    """
    if not is_maf_gemini_ready():
        logger.warning(
            "Microsoft Agent Framework or Google Gemini API key not configured. "
            "Using deterministic analytical intelligence engine."
        )
        return None

    try:
        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if api_key:
            if "GOOGLE_API_KEY" not in os.environ:
                os.environ["GOOGLE_API_KEY"] = api_key
            if "GEMINI_API_KEY" not in os.environ:
                os.environ["GEMINI_API_KEY"] = api_key

        client = GeminiChatClient(
            api_key=api_key,
            model=settings.gemini_model,
        )
        agent = Agent(
            client=client,
            name=name,
            instructions=instructions,
        )
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize MAF Gemini Agent '{name}': {e}")
        return None


def count_gemini_tokens(text: str) -> int:
    """Counts tokens using Google Gemini's native API (models.count_tokens).

    Never relies on static third-party tokenizers like tiktoken.
    """
    if not text or not is_maf_gemini_ready():
        return 0
    try:
        from google import genai

        api_key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        g_client = genai.Client(api_key=api_key)
        res = g_client.models.count_tokens(model=settings.gemini_model, contents=text)
        return int(res.total_tokens)
    except Exception as e:
        logger.warning(f"Gemini native count_tokens API call failed: {e}")
        return 0


def extract_token_usage(resp: Any, prompt_text: str = "") -> Tuple[int, int]:
    """Extracts input and output token counts directly from Gemini response usage_details or Gemini's inbuilt count_tokens API.

    Returns (input_tokens, output_tokens).
    """
    input_tokens = 0
    output_tokens = 0


    if resp is not None and hasattr(resp, "usage_details") and resp.usage_details:
        ud = resp.usage_details
        if isinstance(ud, dict):
            input_tokens = int(ud.get("input_token_count", 0))
            output_tokens = int(ud.get("output_token_count", 0))
        elif hasattr(ud, "input_token_count") and hasattr(ud, "output_token_count"):
            input_tokens = int(getattr(ud, "input_token_count", 0))
            output_tokens = int(getattr(ud, "output_token_count", 0))


    if input_tokens == 0 and prompt_text:
        input_tokens = count_gemini_tokens(prompt_text)


    if output_tokens == 0 and resp is not None and hasattr(resp, "text") and resp.text:
        output_tokens = count_gemini_tokens(resp.text)

    return input_tokens, output_tokens
