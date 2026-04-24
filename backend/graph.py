"""
Graph assembly.
Pipeline: router → (research?) → orchestrator → workers → reducer → seo_meta
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from langgraph.graph import START, END, StateGraph

from backend.schemas import State
from backend.nodes.router import router_node, route_next
from backend.nodes.research import research_node
from backend.nodes.orchestrator import orchestrator_node
from backend.nodes.worker import worker_node, fanout
from backend.nodes.reducer import merge_content, decide_images, generate_and_place_images
from backend.nodes.seo_meta import seo_meta_node


def _build_reducer_subgraph():
    g = StateGraph(State)
    g.add_node("merge_content", merge_content)
    g.add_node("decide_images", decide_images)
    g.add_node("generate_and_place_images", generate_and_place_images)
    g.add_edge(START, "merge_content")
    g.add_edge("merge_content", "decide_images")
    g.add_edge("decide_images", "generate_and_place_images")
    g.add_edge("generate_and_place_images", END)
    return g.compile()


def _build_main_graph():
    reducer_subgraph = _build_reducer_subgraph()

    g = StateGraph(State)
    g.add_node("router", router_node)
    g.add_node("research", research_node)
    g.add_node("orchestrator", orchestrator_node)
    g.add_node("worker", worker_node)
    g.add_node("reducer", reducer_subgraph)
    g.add_node("seo_meta", seo_meta_node)   # ← new SEO node

    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        route_next,
        {"research": "research", "orchestrator": "orchestrator"},
    )
    g.add_edge("research", "orchestrator")
    g.add_conditional_edges("orchestrator", fanout, ["worker"])
    g.add_edge("worker", "reducer")
    g.add_edge("reducer", "seo_meta")       # ← reducer → seo_meta → END
    g.add_edge("seo_meta", END)

    return g.compile()


app = _build_main_graph()


def run(topic: str, as_of: Optional[str] = None) -> dict:
    if as_of is None:
        as_of = date.today().isoformat()

    initial: State = {
        "topic": topic,
        "as_of": as_of,
        "mode": "",
        "needs_research": False,
        "queries": [],
        "recency_days": 7,
        "evidence": [],
        "plan": None,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
        "seo_meta": {},
    }

    out = app.invoke(initial)
    plan = out.get("plan")
    print(f"\n{'='*70}")
    print(f"TOPIC:    {topic}")
    print(f"MODE:     {out.get('mode')}  |  BLOG_KIND: {plan.blog_kind if plan else 'N/A'}")
    print(f"SECTIONS: {len(plan.tasks) if plan else 0}  |  IMAGES: {len(out.get('image_specs', []))}")
    meta = out.get("seo_meta") or {}
    print(f"SEO TITLE: {meta.get('title_tag', 'N/A')}")
    print(f"FOCUS KW:  {meta.get('focus_keyword', 'N/A')}")
    print(f"{'='*70}\n")
    return out


if __name__ == "__main__":
    import sys
    topic = " ".join(sys.argv[1:]) or "Self Attention in Transformer Architecture"
    run(topic)
