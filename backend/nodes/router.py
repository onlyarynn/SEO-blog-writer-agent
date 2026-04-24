"""Router node — decides research mode before planning."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import llm
from backend.schemas import RouterDecision, State


ROUTER_SYSTEM = """\
You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.

Modes:
- closed_book (needs_research=false):
  Evergreen topics — correctness does not depend on recent facts.
  Examples: "Self Attention in Transformers", "Python decorators"

- hybrid (needs_research=true):
  Mostly evergreen but needs up-to-date examples/tools/models.
  Examples: "Best LLMs for coding in 2025", "State of RAG frameworks"

- open_book (needs_research=true):
  Volatile/current: news roundups, "this week", "latest", rankings, pricing.
  Examples: "AI news this week", "Latest OpenAI releases"

If needs_research=true:
- Output 3–10 high-signal, scoped search queries.
- For open_book, include queries reflecting the last 7 days.
- Avoid generic single-word queries like "AI" or "LLM".
"""


def router_node(state: State) -> dict:
    decider = llm.with_structured_output(RouterDecision)
    decision: RouterDecision = decider.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=f"Topic: {state['topic']}\nAs-of date: {state['as_of']}"),
    ])

    if decision.mode == "open_book":
        recency_days = 7
    elif decision.mode == "hybrid":
        recency_days = 45
    else:
        recency_days = 3650

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
        "recency_days": recency_days,
    }


def route_next(state: State) -> str:
    return "research" if state.get("needs_research") else "orchestrator"
