"""Unified multi-model architecture for open research-lite.

Provides distinct model roles:
1. Small Extractor Sub-Model: Fast, cheap model that filters raw web pages into atomic facts.
2. Main Writer Model: High-reasoning model that synthesizes the final intelligence dossier.
"""

import asyncio
import logging
import os
import random
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar
from dotenv import load_dotenv

load_dotenv()

from open_research_lite.exceptions import ConfigurationError

logger = logging.getLogger("open_research_lite.models")

T = TypeVar("T")

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_RETRYABLE_ERROR_KEYWORDS = ("rate limit", "too many requests", "server error", "overloaded", "timeout", "connection")


async def with_retry(
    coro_factory: Callable[[], Coroutine[Any, Any, T]],
    max_attempts: int = 4,
    base_delay: float = 1.5,
    max_delay: float = 60.0,
) -> T:
    """Async exponential backoff retry wrapper for LLM API calls.

    Retries on rate-limit (429), transient server errors (500/502/503/504),
    and any exception whose message contains common transient error keywords.
    Raises the final exception if all attempts are exhausted.
    """
    last_exc: Exception = RuntimeError("No attempts made")
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_factory()
        except Exception as exc:
            last_exc = exc
            exc_msg = str(exc).lower()
            is_retryable = any(kw in exc_msg for kw in _RETRYABLE_ERROR_KEYWORDS)
            # Also check for HTTP status codes embedded in exception messages
            is_retryable = is_retryable or any(
                str(code) in exc_msg for code in _RETRYABLE_STATUS_CODES
            )
            if not is_retryable or attempt == max_attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1), max_delay)
            logger.warning(
                f"LLM call attempt {attempt}/{max_attempts} failed ({exc}). "
                f"Retrying in {delay:.1f}s..."
            )
            await asyncio.sleep(delay)
    raise last_exc



SMALL_EXTRACTOR_MODELS: List[Dict[str, str]] = [
    {"id": "gemini-2.5-flash", "label": "Google - Gemini 2.5 Flash (Ultra-fast, 1M context - Recommended for Fast LLM)"},
    {"id": "gpt-4o-mini", "label": "OpenAI - GPT-4o Mini (Cost-efficient, high-speed extraction)"},
    {"id": "claude-3-5-haiku-latest", "label": "Anthropic - Claude 3.5 Haiku (Sub-second extraction latency)"},
    {"id": "llama-3.1-8b-instant", "label": "Meta - Llama 3.1 8B via Groq (Ultra-fast open-source extraction)"},
    {"id": "deepseek-chat", "label": "DeepSeek - DeepSeek-V3 (High-throughput, cost-effective extraction)"},
    {"id": "mistral-small-latest", "label": "Mistral - Mistral Small (Fast European extraction model)"},
]

MAIN_WRITER_MODELS: List[Dict[str, str]] = [
    {"id": "gemini-2.5-flash", "label": "Google - Gemini 2.5 Flash (Fast, high-signal report generation - Recommended)"},
    {"id": "claude-3-5-sonnet-latest", "label": "Anthropic - Claude 3.5 Sonnet (State-of-the-art analytical synthesis)"},
    {"id": "gpt-4o", "label": "OpenAI - GPT-4o (Flagship reasoning & writing)"},
    {"id": "gpt-4.1", "label": "OpenAI - GPT-4.1 (High-precision research report)"},
    {"id": "gemini-2.5-pro", "label": "Google - Gemini 2.5 Pro (Deep complex analysis)"},
    {"id": "o1", "label": "OpenAI - o1 (Deliberative step-by-step reasoning)"},
    {"id": "o3-mini", "label": "OpenAI - o3 Mini (STEM and logic specialist)"},
    {"id": "claude-3-opus-latest", "label": "Anthropic - Claude 3 Opus (Comprehensive exhaustive synthesis)"},
    {"id": "deepseek-reasoner", "label": "DeepSeek - DeepSeek-R1 (Advanced chain-of-thought)"},
    {"id": "deepseek-chat", "label": "DeepSeek - DeepSeek-V3 (Open foundation intelligence)"},
    {"id": "llama-3.3-70b-versatile", "label": "Meta - Llama 3.3 70B via Groq (Top open-source model)"},
    {"id": "mistral-large-latest", "label": "Mistral - Mistral Large (Flagship European model)"},
]

# Combined list for general lookups
AVAILABLE_MODELS = SMALL_EXTRACTOR_MODELS + MAIN_WRITER_MODELS


def resolve_api_key(model_name: str) -> Optional[str]:
    """Auto-resolves the matching environment API key for a model."""
    m = model_name.lower().strip()
    if "claude" in m:
        return os.getenv("ANTHROPIC_API_KEY")
    elif "deepseek" in m:
        return os.getenv("DEEPSEEK_API_KEY")
    elif any(k in m for k in ("llama", "mixtral", "qwen")):
        return os.getenv("GROQ_API_KEY")
    elif "gpt" in m or m.startswith("o1") or m.startswith("o3"):
        return os.getenv("OPENAI_API_KEY")
    elif "mistral" in m:
        return os.getenv("MISTRAL_API_KEY")
    elif "gemini" in m:
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return None


def get_env_var_for_model(model_name: str) -> str:
    """Returns the primary environment variable name for a given model."""
    m = model_name.lower().strip()
    if "claude" in m:
        return "ANTHROPIC_API_KEY"
    elif "deepseek" in m:
        return "DEEPSEEK_API_KEY"
    elif any(k in m for k in ("llama", "mixtral", "qwen")):
        return "GROQ_API_KEY"
    elif "gpt" in m or m.startswith("o1") or m.startswith("o3"):
        return "OPENAI_API_KEY"
    elif "mistral" in m:
        return "MISTRAL_API_KEY"
    elif "gemini" in m:
        return "GEMINI_API_KEY"
    return "API_KEY"



def get_default_models() -> tuple[str, str]:
    """Auto-detects the optimal (extractor_model, writer_model) based on configured environment keys."""
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini-2.5-flash", "gemini-2.5-flash"
    elif os.getenv("OPENAI_API_KEY"):
        return "gpt-4o-mini", "gpt-4o"
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"
    elif os.getenv("GROQ_API_KEY"):
        return "llama-3.1-8b-instant", "llama-3.3-70b-versatile"
    elif os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek-chat", "deepseek-reasoner"
    elif os.getenv("MISTRAL_API_KEY"):
        return "mistral-small-latest", "mistral-large-latest"
    return "gemini-2.5-flash", "gemini-2.5-flash"


def get_chat_model(
    model_name: str, 
    api_key: Optional[str] = None, 
    max_tokens: Optional[int] = None
) -> Any:
    """Instantiates the appropriate chat model across major providers without artificial token constraints."""
    model_lower = model_name.lower().strip()

    if "claude" in model_lower:
        from langchain_anthropic import ChatAnthropic
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ConfigurationError(f"Anthropic API key missing for '{model_name}'. Set ANTHROPIC_API_KEY.")
        # ChatAnthropic requires max_tokens to be set; resolve to the model's native maximum allowed output tokens
        anthropic_kwargs: Dict[str, Any] = {"model": model_name, "api_key": key, "temperature": 0.1}
        if max_tokens is not None:
            anthropic_kwargs["max_tokens"] = max_tokens
        else:
            if "3-7" in model_lower:
                anthropic_kwargs["max_tokens"] = 64000
            elif "3-5" in model_lower:
                anthropic_kwargs["max_tokens"] = 8192
            elif "opus" in model_lower:
                anthropic_kwargs["max_tokens"] = 4096
            else:
                anthropic_kwargs["max_tokens"] = 8192
        return ChatAnthropic(**anthropic_kwargs)

    elif "deepseek" in model_lower:
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise ConfigurationError(f"DeepSeek API key missing for '{model_name}'. Set DEEPSEEK_API_KEY.")
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "api_key": key,
            "base_url": "https://api.deepseek.com",
            "temperature": 0.1,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    elif "mistral" in model_lower:
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("MISTRAL_API_KEY")
        if not key:
            raise ConfigurationError(f"Mistral API key missing for '{model_name}'. Set MISTRAL_API_KEY.")
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "api_key": key,
            "base_url": "https://api.mistral.ai/v1",
            "temperature": 0.1,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    elif any(k in model_lower for k in ("llama", "mixtral", "qwen")):
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ConfigurationError(f"Groq API key missing for '{model_name}'. Set GROQ_API_KEY.")
        kwargs: Dict[str, Any] = {
            "model": model_name,
            "api_key": key,
            "base_url": "https://api.groq.com/openai/v1",
            "temperature": 0.1,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)

    elif "gpt" in model_lower or model_lower.startswith("o1") or model_lower.startswith("o3"):
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ConfigurationError(f"OpenAI API key missing for '{model_name}'. Set OPENAI_API_KEY.")
        if model_lower.startswith("o1") or model_lower.startswith("o3"):
            o_kwargs: Dict[str, Any] = {"model": model_name, "api_key": key}
            if max_tokens is not None:
                o_kwargs["max_completion_tokens"] = max_tokens
            return ChatOpenAI(**o_kwargs)
        g_kwargs: Dict[str, Any] = {"model": model_name, "api_key": key, "temperature": 0.1}
        if max_tokens is not None:
            g_kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**g_kwargs)

    else:
        # Default: Google Gemini
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ConfigurationError(f"Google Gemini API key missing for '{model_name}'. Set GEMINI_API_KEY or GOOGLE_API_KEY.")
        actual_model = model_name if "gemini" in model_lower else "gemini-2.5-flash"
        gemini_kwargs: Dict[str, Any] = {"model": actual_model, "google_api_key": key, "temperature": 0.1}
        if max_tokens is not None:
            gemini_kwargs["max_output_tokens"] = max_tokens
        return ChatGoogleGenerativeAI(**gemini_kwargs)

