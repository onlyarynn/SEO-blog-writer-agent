"""
LLM configuration — lazy initialization so secrets are always available.
The LLM is NOT created at import time. It is created on first use.

Fix for Streamlit Cloud: secrets are injected into os.environ BEFORE
any API key lookup, guaranteeing the key is available when the LLM is built.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_llm_instance = None


def _inject_streamlit_secrets() -> None:
    """
    Pushes ALL Streamlit secrets into os.environ so every downstream
    library (anthropic, langchain, tavily, etc.) picks them up naturally.
    This is safe to call multiple times — it is a no-op if st is unavailable.
    """
    try:
        import streamlit as st
        for key, value in st.secrets.items():
            # Only inject strings; skip nested TOML tables
            if isinstance(value, str) and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass  # Running outside Streamlit — .env / real env vars take over


def _get_key() -> str:
    """Return ANTHROPIC_API_KEY from environment (after secrets injection)."""
    _inject_streamlit_secrets()
    return os.environ.get("ANTHROPIC_API_KEY", "")


def _get_llm():
    """Return the singleton LLM instance, creating it on first call."""
    global _llm_instance
    if _llm_instance is None:
        key = _get_key()
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Add it to Streamlit Cloud → Settings → Secrets, "
                "or to your local .env file."
            )
        os.environ["ANTHROPIC_API_KEY"] = key  # ensure child processes see it

        from langchain_anthropic import ChatAnthropic
        _llm_instance = ChatAnthropic(
            model="claude-sonnet-4-5",
            temperature=0.3,
            max_tokens=4096,
        )
    return _llm_instance


class _LazyLLM:
    """
    Proxy object that behaves like a ChatAnthropic instance but defers
    initialisation to the first method call — after Streamlit secrets
    have been injected.
    """

    def __getattr__(self, name):
        return getattr(_get_llm(), name)

    def invoke(self, *args, **kwargs):
        return _get_llm().invoke(*args, **kwargs)

    def with_structured_output(self, *args, **kwargs):
        return _get_llm().with_structured_output(*args, **kwargs)

    def stream(self, *args, **kwargs):
        return _get_llm().stream(*args, **kwargs)


# Module-level singleton — safe to import at any time
llm = _LazyLLM()
