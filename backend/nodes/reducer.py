"""
Reducer subgraph — 3 sequential nodes after all workers complete:
  merge_content → decide_images → generate_and_place_images
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from backend.llm import llm
from backend.schemas import GlobalImagePlan, State

OUTPUTS_DIR = Path("outputs")


def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


# ── Node 1: merge_content ────────────────────────────────────

def merge_content(state: State) -> dict:
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without a plan.")
    ordered = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered).strip()
    return {"merged_md": f"# {plan.blog_title}\n\n{body}\n"}


# ── Node 2: decide_images ────────────────────────────────────

DECIDE_IMAGES_SYSTEM = """\
You are an expert technical editor reviewing a completed blog post.
Decide whether diagrams would materially improve reader understanding.

Rules:
- Maximum 3 images total.
- Only suggest images that genuinely help: architecture diagrams, flow charts,
  data-flow visuals, comparison tables rendered as visuals, etc.
- Avoid decorative images. Prefer labeled technical diagrams.
- Insert placeholders EXACTLY as: [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]]
- If no images are needed: set md_with_placeholders to the FULL original
  markdown (do not leave it empty), and set images=[].
- Always return md_with_placeholders — it must contain the full blog markdown.
- Write detailed prompts: specify diagram type, components, labels, layout, style.

IMPORTANT: md_with_placeholders is required. Always return it with the
full markdown content, even if no images are needed.
"""


def decide_images(state: State) -> dict:
    planner = llm.with_structured_output(GlobalImagePlan)
    merged_md = state["merged_md"]

    try:
        image_plan: GlobalImagePlan = planner.invoke([
            SystemMessage(content=DECIDE_IMAGES_SYSTEM),
            HumanMessage(content=(
                f"Blog kind: {state['plan'].blog_kind}\n"
                f"Topic: {state['topic']}\n\n"
                f"Return the full markdown in md_with_placeholders "
                f"(with [[IMAGE_N]] tags inserted where helpful, or unchanged if no images needed):\n\n"
                f"{merged_md}"
            )),
        ])

        # Fallback: if Claude returned empty md_with_placeholders, use the original
        final_md = image_plan.md_with_placeholders.strip()
        if not final_md:
            final_md = merged_md

        return {
            "md_with_placeholders": final_md,
            "image_specs": [img.model_dump() for img in image_plan.images],
        }

    except Exception:
        # If the whole call fails, skip images gracefully
        return {
            "md_with_placeholders": merged_md,
            "image_specs": [],
        }


# ── Image generation backends ────────────────────────────────

def _generate_with_gemini(prompt: str) -> bytes:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not set.")
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            safety_settings=[types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_ONLY_HIGH",
            )],
        ),
    )
    parts = getattr(resp, "parts", None)
    if not parts and getattr(resp, "candidates", None):
        try:
            parts = resp.candidates[0].content.parts
        except Exception:
            parts = None
    if not parts:
        raise RuntimeError("No image content returned from Gemini.")
    for part in parts:
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            return inline.data
    raise RuntimeError("No inline image bytes in Gemini response.")


def _ascii_diagram_fallback(spec: dict) -> str:
    try:
        response = llm.invoke([
            SystemMessage(content=(
                "Generate a clear ASCII/text diagram for the concept described. "
                "Return ONLY the diagram inside a markdown code fence (```). "
                "Keep it under 25 lines. Label all components."
            )),
            HumanMessage(content=(
                f"Alt: {spec.get('alt', '')}\n"
                f"Caption: {spec.get('caption', '')}\n"
                f"Prompt: {spec.get('prompt', '')}"
            )),
        ])
        return f"\n{response.content.strip()}\n*{spec.get('caption', '')}*\n"
    except Exception:
        return f"\n> **[Diagram: {spec.get('caption', '')}]**\n"


# ── Node 3: generate_and_place_images ───────────────────────

def generate_and_place_images(state: State) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state.get("merged_md", "")
    image_specs: List[dict] = state.get("image_specs", []) or []

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    if not image_specs:
        out_path = OUTPUTS_DIR / f"{_safe_slug(plan.blog_title)}.md"
        out_path.write_text(md, encoding="utf-8")
        return {"final": md}

    images_dir = OUTPUTS_DIR / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    gemini_ok = bool(os.getenv("GOOGLE_API_KEY"))

    for spec in image_specs:
        placeholder = spec["placeholder"]
        out_path = images_dir / spec["filename"]

        if gemini_ok and not out_path.exists():
            try:
                img_bytes = _generate_with_gemini(spec["prompt"])
                out_path.write_bytes(img_bytes)
            except Exception:
                gemini_ok = False
                md = md.replace(placeholder, _ascii_diagram_fallback(spec))
                continue

        if out_path.exists():
            img_md = f"![{spec['alt']}](outputs/images/{spec['filename']})\n*{spec['caption']}*"
            md = md.replace(placeholder, img_md)
        else:
            md = md.replace(placeholder, _ascii_diagram_fallback(spec))

    final_path = OUTPUTS_DIR / f"{_safe_slug(plan.blog_title)}.md"
    final_path.write_text(md, encoding="utf-8")
    return {"final": md}
