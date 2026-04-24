"""
SEO Meta node — runs after reducer, generates:
  - SEO title tag (< 60 chars)
  - Meta description (< 160 chars)
  - Focus keyword + semantic keywords
  - FAQ schema (JSON-LD) for AI Overview eligibility
  - Readability + E-E-A-T checklist score
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import llm
from backend.schemas import State


class FAQItem(BaseModel):
    question: str
    answer: str = Field(..., description="Concise answer, 40–80 words.")


class SEOMeta(BaseModel):
    title_tag: str = Field(..., description="SEO title tag, max 60 characters.")
    meta_description: str = Field(..., description="Meta description, max 160 characters.")
    focus_keyword: str = Field(..., description="Primary keyword this blog targets.")
    semantic_keywords: List[str] = Field(
        ..., description="5–10 related LSI/semantic keywords to naturally include."
    )
    faq_items: List[FAQItem] = Field(
        ..., description="3–5 FAQ pairs eligible for Google FAQ schema."
    )
    eeat_notes: List[str] = Field(
        ..., description="2–4 specific suggestions to improve E-E-A-T in this blog."
    )
    canonical_slug: str = Field(
        ..., description="URL-friendly slug, e.g. 'self-attention-transformer-guide'."
    )


SEO_META_SYSTEM = """\
You are an SEO strategist specialising in Google's Helpful Content System
and E-E-A-T signals (2025/2026).

Given a completed blog post, produce:
1. An SEO title tag (≤ 60 chars) that includes the focus keyword naturally.
2. A meta description (≤ 160 chars) that summarises the value and includes
   the keyword. Must read naturally — not stuffed.
3. Focus keyword: the single most important search term this post targets.
4. 5–10 semantic/LSI keywords that should appear naturally in the content.
5. 3–5 FAQ items eligible for Google FAQ Schema / AI Overview citations.
   - Questions must match real "People Also Ask" style queries.
   - Answers must be 40–80 words: direct, factual, no fluff.
6. 2–4 concrete E-E-A-T improvement notes for this specific post.
7. A canonical URL slug (lowercase, hyphens, no stop words).

Output must match the SEOMeta schema exactly.
"""


def seo_meta_node(state: State) -> dict:
    """
    Generates SEO metadata from the finished blog.
    Appends FAQ JSON-LD schema and keyword block to the final markdown.
    """
    final_md = state.get("final", "")
    if not final_md:
        return {}

    generator = llm.with_structured_output(SEOMeta)

    try:
        meta: SEOMeta = generator.invoke([
            SystemMessage(content=SEO_META_SYSTEM),
            HumanMessage(content=(
                f"Blog markdown:\n\n{final_md[:6000]}"  # trim to avoid token overflow
            )),
        ])
    except Exception:
        return {}  # SEO meta failure should never block the blog

    # Build FAQ JSON-LD block to append to markdown
    faq_jsonld = _build_faq_jsonld(meta.faq_items)

    # Build readable SEO summary block
    seo_block = _build_seo_block(meta)

    # Append both to the final markdown
    enhanced_md = final_md.rstrip() + "\n\n" + seo_block + "\n\n" + faq_jsonld

    # Overwrite the saved file with the enhanced version
    from pathlib import Path
    import re
    slug = meta.canonical_slug or _fallback_slug(state.get("topic", "blog"))
    out_path = Path("outputs") / f"{slug}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(enhanced_md, encoding="utf-8")

    return {
        "final": enhanced_md,
        "seo_meta": meta.model_dump(),
    }


def _build_seo_block(meta: SEOMeta) -> str:
    keywords_line = ", ".join(f"`{k}`" for k in meta.semantic_keywords)
    eeat_lines = "\n".join(f"- {note}" for note in meta.eeat_notes)
    return (
        "---\n"
        "## 📋 SEO Metadata\n\n"
        f"**Title tag:** {meta.title_tag}  \n"
        f"**Meta description:** {meta.meta_description}  \n"
        f"**Focus keyword:** `{meta.focus_keyword}`  \n"
        f"**Semantic keywords:** {keywords_line}  \n"
        f"**Canonical slug:** `/{meta.canonical_slug}/`  \n\n"
        "### ✅ E-E-A-T Improvement Notes\n"
        f"{eeat_lines}\n"
        "---"
    )


def _build_faq_jsonld(faq_items: List[FAQItem]) -> str:
    if not faq_items:
        return ""

    entities = []
    for item in faq_items:
        # Escape quotes for JSON safety
        q = item.question.replace('"', '\\"')
        a = item.answer.replace('"', '\\"')
        entities.append(
            f'    {{\n'
            f'      "@type": "Question",\n'
            f'      "name": "{q}",\n'
            f'      "acceptedAnswer": {{\n'
            f'        "@type": "Answer",\n'
            f'        "text": "{a}"\n'
            f'      }}\n'
            f'    }}'
        )

    entities_str = ",\n".join(entities)
    return (
        "<!-- FAQ Schema (paste into your page <head> or use a plugin) -->\n"
        "```json\n"
        "{\n"
        '  "@context": "https://schema.org",\n'
        '  "@type": "FAQPage",\n'
        '  "mainEntity": [\n'
        f"{entities_str}\n"
        "  ]\n"
        "}\n"
        "```"
    )


def _fallback_slug(text: str) -> str:
    import re
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:60] or "blog"
