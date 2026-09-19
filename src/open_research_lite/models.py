"""Unified multi-model architecture for open research-lite.

Provides distinct model roles:
1. Small Extractor Sub-Model: Fast, cheap model that filters raw web pages into atomic facts.
2. Main Writer Model: High-reasoning model that synthesizes the final intelligence dossier.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

from open_research_lite.exceptions import ConfigurationError


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
        # ChatAnthropic requires max_tokens; default to full standard model capability (8,192) or user override
        token_cap = max_tokens or 8192
        return ChatAnthropic(model=model_name, api_key=key, temperature=0.1, max_tokens=token_cap)

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

