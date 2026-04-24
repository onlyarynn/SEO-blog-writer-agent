"""Worker node — writes one E-E-A-T and SEO optimized blog section."""
from __future__ import annotations

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import Send

from backend.llm import llm
from backend.schemas import EvidenceItem, Plan, State, Task


WORKER_SYSTEM = """\
You are a senior technical writer, domain expert, and SEO strategist.
Write ONE section of a blog post that satisfies Google's 2025/2026
Helpful Content System and E-E-A-T signals.

════════════════════════════════════════
GOOGLE CONTENT RULES — apply to every section:
════════════════════════════════════════

E-E-A-T SIGNALS:
- Write as a practitioner who has *done* this, not as someone summarizing docs.
- Use first-person practitioner voice where natural:
  "In practice, this means...", "A common mistake here is...",
  "The non-obvious gotcha is...", "Teams often overlook..."
- Avoid vague claims. Every assertion should be specific and verifiable.
- If the section tag includes "opinion" or "original-insight", express a
  clear, reasoned position — don't hedge everything.

HELPFUL CONTENT (for people, not bots):
- Answer the section's Goal directly in the first 2 sentences.
- No throat-clearing intros like "In this section we will explore..."
- No filler conclusions like "As we can see, X is very important."
- Every paragraph must add new information — no rephrasing the previous one.

FEATURED SNIPPET & AI OVERVIEW ELIGIBILITY:
- If the section can be expressed as a definition, a numbered list of steps,
  or a comparison table — DO IT. These formats are prioritized by Google's
  AI Overviews and Featured Snippets.
- Use a concise answer in the first 40–60 words if the section answers a
  "what is" or "how to" question. This is the snippet target.

SEMANTIC DEPTH:
- Naturally mention related concepts, tools, and entities — don't keyword-stuff,
  but don't omit important related terms either.
- Include concrete specifics: numbers, names, versions, benchmarks where known.

SCANNABILITY:
- Use ## for section heading (match a natural search query where possible).
- Use ### subheadings for multi-part sections.
- Short paragraphs (3–5 lines max). Use bullet lists for parallel items.
- Bold the single most important takeaway per section.

════════════════════════════════════════
HARD CONSTRAINTS:
════════════════════════════════════════
- Cover ALL bullets in order. Do not skip or merge any.
- Stay within ±15% of the target word count.
- Output ONLY the section markdown — no H1 title, no meta-commentary.
- Start with ## heading that reads like a natural search query.

SCOPE GUARD:
- If blog_kind == "news_roundup": summarize events + implications only.
  Do NOT drift into tutorials or how-to guides.

GROUNDING:
- If mode == "open_book": only state specific events/claims supported by
  provided Evidence URLs. Attach as Markdown links ([Source](URL)).
  Write "Not found in provided sources." for unsupported claims.
- If requires_citations == true: cite Evidence URLs for external claims.

CODE:
- If requires_code == true: include at least one minimal, correct,
  idiomatic snippet. Add a comment explaining the non-obvious parts.
"""


def worker_node(payload: dict) -> dict:
    task = Task(**payload["task"])
    plan = Plan(**payload["plan"])
    evidence: List[EvidenceItem] = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    topic: str = payload["topic"]
    mode: str = payload.get("mode", "closed_book")
    as_of: str = payload.get("as_of", "")
    recency_days: int = payload.get("recency_days", 3650)

    bullets_text = "\n- " + "\n- ".join(task.bullets)
    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}"
            for e in evidence[:20]
        )

    # Detect if section needs special SEO treatment
    is_original = any(t in ["opinion", "original-insight"] for t in (task.tags or []))
    is_snippet_candidate = any(
        kw in task.title.lower()
        for kw in ["what is", "how to", "why", "best", "vs", "compare", "difference"]
    )

    seo_hints = []
    if is_original:
        seo_hints.append("This section should express a clear, opinionated take backed by reasoning.")
    if is_snippet_candidate:
        seo_hints.append(
            "Lead with a direct 40–60 word answer to make this snippet-eligible for Google Featured Snippets."
        )

    section_md: str = llm.invoke([
        SystemMessage(content=WORKER_SYSTEM),
        HumanMessage(content=(
            f"Blog title: {plan.blog_title}\n"
            f"Audience: {plan.audience}\n"
            f"Tone: {plan.tone}\n"
            f"Blog kind: {plan.blog_kind}\n"
            f"Topic: {topic}\n"
            f"Mode: {mode}\n"
            f"As-of: {as_of} (recency_days={recency_days})\n\n"
            f"Section title: {task.title}\n"
            f"Goal: {task.goal}\n"
            f"Target words: {task.target_words}\n"
            f"Tags: {task.tags}\n"
            f"requires_research: {task.requires_research}\n"
            f"requires_citations: {task.requires_citations}\n"
            f"requires_code: {task.requires_code}\n"
            f"Bullets:{bullets_text}\n\n"
            + (f"SEO hints for this section:\n- " + "\n- ".join(seo_hints) + "\n\n" if seo_hints else "")
            + f"Evidence (ONLY cite these URLs):\n{evidence_text}\n"
        )),
    ]).content.strip()

    return {"sections": [(task.id, section_md)]}


def fanout(state: State) -> list:
    assert state["plan"] is not None
    return [
        Send("worker", {
            "task": task.model_dump(),
            "topic": state["topic"],
            "mode": state["mode"],
            "as_of": state["as_of"],
            "recency_days": state["recency_days"],
            "plan": state["plan"].model_dump(),
            "evidence": [e.model_dump() for e in state.get("evidence", [])],
        })
        for task in state["plan"].tasks
    ]
