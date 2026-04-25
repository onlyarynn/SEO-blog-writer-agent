"""
LLM configuration — lazy initialization so secrets are always available.
The LLM is NOT created at import time. It is created on first use.
This fixes the Streamlit Cloud issue where os.environ is not populated
at module import time.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

_llm_instance = None


def _get_key() -> str:
    """Read ANTHROPIC_API_KEY from every possible source."""
    # 1. Already in environment (Streamlit Cloud injects secrets here)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key

    # 2. Try st.secrets (fallback for edge cases)
    try:
        import streamlit as st
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            os.environ["ANTHROPIC_API_KEY"] = key
            return key
    except Exception:
        pass

    return ""


def _get_llm():
    """Return the LLM instance, creating it on first call."""
    global _llm_instance
    if _llm_instance is None:
        key = _get_key()
        if not key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in Streamlit Cloud Secrets or your local .env file."
            )
        os.environ["ANTHROPIC_API_KEY"] = key

        from langchain_anthropic import ChatAnthropic
        _llm_instance = ChatAnthropic(
            model="claude-sonnet-4-5",
            temperature=0.3,
            max_tokens=4096,
        )
    return _llm_instance


class _LazyLLM:
    """
    Proxy object that behaves like a ChatAnthropic instance
    but initializes it only on first method call.
    """
    def __getattr__(self, name):
        return getattr(_get_llm(), name)

    def invoke(self, *args, **kwargs):
        return _get_llm().invoke(*args, **kwargs)

    def with_structured_output(self, *args, **kwargs):
        return _get_llm().with_structured_output(*args, **kwargs)

    def stream(self, *args, **kwargs):
        return _get_llm().stream(*args, **kwargs)


# This is what all nodes import — safe at module level
llm = _LazyLLM()
