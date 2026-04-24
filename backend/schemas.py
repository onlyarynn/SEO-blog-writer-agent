"""
All Pydantic models AND the shared LangGraph State TypedDict.
Keeping State here breaks the circular import:
  graph.py → nodes/*.py → graph.py (was circular before)
"""
from __future__ import annotations

import operator
from typing import Annotated, List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# Blog planning schemas
# ─────────────────────────────────────────────────────────────

class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="One sentence: what the reader will understand/do after this section.")
    bullets: List[str] = Field(..., min_length=3, max_length=6)
    target_words: int = Field(..., description="Target word count (120–550).")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    reason: str
    queries: List[str] = Field(default_factory=list)
    max_results_per_query: int = Field(5)


class ImageSpec(BaseModel):
    placeholder: str
    filename: str
    alt: str
    caption: str
    prompt: str
    size: Literal["1024x1024", "1024x1536", "1536x1024"] = "1024x1024"
    quality: Literal["low", "medium", "high"] = "medium"


class GlobalImagePlan(BaseModel):
    md_with_placeholders: str = Field(default="")
    images: List[ImageSpec] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# LangGraph shared State — lives here to avoid circular imports
# ─────────────────────────────────────────────────────────────

class State(TypedDict):
    # User input
    topic: str
    as_of: str

    # Router outputs
    mode: str
    needs_research: bool
    queries: List[str]
    recency_days: int

    # Research output
    evidence: List[EvidenceItem]

    # Orchestrator output
    plan: Optional[Plan]

    # Worker outputs — operator.add collects all tuples
    sections: Annotated[List[tuple], operator.add]

    # Reducer subgraph state
    merged_md: str
    md_with_placeholders: str = Field(default="")
    image_specs: List[dict]

    # Final output
    final: str
    seo_meta: dict  # populated by seo_meta_node
