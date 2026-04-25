"""LLM configuration — Anthropic Claude via langchain-anthropic."""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# On Streamlit Cloud, secrets live in st.secrets not os.environ.
# We read from st.secrets first, then fall back to os.getenv (local .env).
try:
    import streamlit as st
    _key = (
        st.secrets.get("ANTHROPIC_API_KEY", "")
        or os.getenv("ANTHROPIC_API_KEY", "")
    )
except Exception:
    _key = os.getenv("ANTHROPIC_API_KEY", "")

if not _key:
    raise ValueError(
        "ANTHROPIC_API_KEY is not set. "
        "Add it to Streamlit Cloud secrets or your local .env file."
    )

os.environ["ANTHROPIC_API_KEY"] = _key

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    temperature=0.3,
    max_tokens=4096,
)
