# 🤖 AI Blog Writer Agent (Anthropic Edition)

A production-style AI agent built with **LangGraph + Claude (Anthropic)** that generates full technical blog posts end-to-end.

## Architecture

```
Topic Input
    │
    ▼
┌─────────┐
│  Router │ ← Decides: closed_book / hybrid / open_book
└────┬────┘
     │
     ▼ (if needs_research)
┌──────────┐
│ Research │ ← Tavily web search + evidence synthesis
└────┬─────┘
     │
     ▼
┌──────────────┐
│ Orchestrator │ ← Plans 5-9 blog sections (structured output)
└──────┬───────┘
       │ fanout (parallel)
   ┌───┴───┐
   │Workers│ ← Each writes one section concurrently
   └───┬───┘
       │ reduce
┌──────┴──────────┐
│  Reducer Graph  │ ← merge → decide_images → generate_images
└─────────────────┘
       │
       ▼
  Final Blog (Markdown + Images)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | **Claude claude-sonnet-4-6** (Anthropic) |
| Orchestration | LangGraph |
| Research | Tavily Search |
| Image Generation | Anthropic `claude-sonnet-4-6` (SVG/text diagrams) or Gemini (optional) |
| Frontend | Streamlit |

## Phases

| Phase | What you build |
|-------|---------------|
| 1 | Project setup + environment |
| 2 | Schemas (Pydantic models) |
| 3 | Basic Agent (orchestrator + workers + reducer) |
| 4 | Router + Research (Tavily) |
| 5 | Image generation node |
| 6 | Streamlit frontend |
| 7 | Production hardening |

## Quick Start

```bash
# 1. Clone / enter project
cd blog-writer-agent

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set API keys
cp .env.example .env
# Edit .env and fill in your keys

# 5. Run frontend
streamlit run frontend/app.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | Your Anthropic API key |
| `TAVILY_API_KEY` | Optional | Enables web research (open_book/hybrid mode) |
| `GOOGLE_API_KEY` | Optional | Enables Gemini image generation |

## Project Structure

```
blog-writer-agent/
├── .env.example
├── requirements.txt
├── README.md
├── backend/
│   ├── __init__.py
│   ├── schemas.py          # All Pydantic models
│   ├── llm.py              # Anthropic LLM configuration
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── router.py       # Routing node
│   │   ├── research.py     # Tavily research node
│   │   ├── orchestrator.py # Planning node
│   │   ├── worker.py       # Section-writing node
│   │   └── reducer.py      # Merge + image nodes
│   └── graph.py            # LangGraph assembly
├── frontend/
│   └── app.py              # Streamlit UI
└── outputs/                # Generated blogs saved here
```
