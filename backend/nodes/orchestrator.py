"""Orchestrator node — creates the structured blog plan with SEO/E-E-A-T alignment."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import llm
from backend.schemas import Plan, State


ORCH_SYSTEM = """\
You are a senior technical writer, developer advocate, and SEO strategist.
Produce a highly actionable outline for a blog post that ranks on Google
and satisfies Google's 2025/2026 Helpful Content System and E-E-A-T signals.

════════════════════════════════════════
GOOGLE CONTENT ALIGNMENT RULES (apply to every plan):
════════════════════════════════════════

1. SEARCH INTENT FIRST
   - Identify the PRIMARY search intent (informational / navigational /
     commercial / transactional) and build the entire plan around it.
   - The blog must answer the reader's real question — not a padded version of it.

2. E-E-A-T (Experience · Expertise · Authoritativeness · Trustworthiness)
   - Include at least ONE section that demonstrates first-hand experience
     or unique perspective (e.g. "What we found when testing X", "Common
     mistakes practitioners make", "Our benchmarks show...").
   - Cite evidence/sources where claims are volatile (requires_citations=True).
   - Avoid unverifiable superlatives ("the best", "most powerful") without data.

3. HELPFUL CONTENT (written for people, not search engines)
   - Every section must answer a question a real reader would ask.
   - No filler sections. No "In conclusion, we have learned..." padding.
   - Include a "Who this is for" or clear audience signal in the intro task.

4. SEMANTIC COMPLETENESS
   - Cover the topic's key sub-entities and related concepts.
   - Plan must include sections for: context/why-it-matters, core mechanics,
     practical application, common pitfalls, and forward-looking implications.
   - This signals topical authority to Google.

5. SCANNABILITY & FEATURED SNIPPET ELIGIBILITY
   - At least ONE section should be structured as a definition, step-by-step
     list, or comparison table — these are eligible for Google Featured Snippets
     and AI Overview citations.
   - Use clear H2 headings that match natural language search queries
     (e.g. "How does X work?" not "X Mechanics").

6. ORIGINALITY SIGNALS
   - Include at least ONE section with an opinionated take, ranking,
     or counter-intuitive finding — something that can't be found by
     aggregating 5 other articles.
   - Mark these sections with tags: ["original-insight"] or ["opinion"].

════════════════════════════════════════
STRUCTURAL REQUIREMENTS:
════════════════════════════════════════
- Create 6–9 sections (tasks).
- Each task: goal (1 sentence) + 3–6 bullets + target_words (150–550).
- Ensure at least 2 sections have requires_code=True (for technical topics).
- For news_roundup: focus on implications, not just summaries.
- Output must strictly match the Plan schema.
"""


def orchestrator_node(state: State) -> dict:
    planner = llm.with_structured_output(Plan)
    mode = state.get("mode", "closed_book")
    evidence = state.get("evidence", []) or []
    forced_kind = "news_roundup" if mode == "open_book" else None

    plan: Plan = planner.invoke([
        SystemMessage(content=ORCH_SYSTEM),
        HumanMessage(content=(
            f"Topic: {state['topic']}\n"
            f"Mode: {mode}\n"
            f"As-of: {state['as_of']} (recency_days={state['recency_days']})\n"
            f"{'Force blog_kind=news_roundup — no tutorial drift.' if forced_kind else ''}\n\n"
            f"Evidence (ONLY use for fresh claims; may be empty):\n"
            f"{[e.model_dump() for e in evidence][:16]}"
        )),
    ])

    if forced_kind:
        plan.blog_kind = "news_roundup"

    return {"plan": plan}
