"""
PHASE 3 — LLM Setup
Configures the Anthropic Claude model via langchain-anthropic.

Key difference from original:
  Original: ChatOpenAI(model="gpt-4.1-mini")
  This:     ChatAnthropic(model="claude-sonnet-4-6")

ChatAnthropic supports .with_structured_output() just like ChatOpenAI,
using Claude's native tool-use under the hood for reliable JSON extraction.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

load_dotenv()

# Primary model — used for all planning, routing, and writing nodes.
# claude-sonnet-4-6 is the recommended balance of speed + quality.
llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    temperature=0.3,          # Low temp = more consistent structured outputs
    max_tokens=4096,          # Enough for long blog sections
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# Fast model — can be used for simple classification tasks like routing.
# Uncomment to use claude-haiku-4-5 for router/research synthesis nodes.
# llm_fast = ChatAnthropic(
#     model="claude-haiku-4-5-20251001",
#     temperature=0.1,
#     max_tokens=2048,
#     anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
# )
