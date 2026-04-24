"""LLM configuration — Anthropic Claude via langchain-anthropic."""
from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# Ensure the key is set in environment before initialising the client
_key = os.getenv("ANTHROPIC_API_KEY", "")
if _key:
    os.environ["ANTHROPIC_API_KEY"] = _key

from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-sonnet-4-5",
    temperature=0.3,
    max_tokens=4096,
)
