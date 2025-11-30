# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A crewAI multi-agent system that monitors news about Members of Parliament (MPs) and delivers curated strategic reports via email. The system uses a two-phase architecture: parallel search followed by sequential analysis.

## Commands

```bash
# Install dependencies (requires uv)
crewai install

# Run the full pipeline
crewai run
```

## Architecture

### Two-Phase Execution Model

**Phase 1: Parallel Search** (`search_service.py` + `search_crew.py`)
- Python controls iteration over MPs using `kickoff_for_each_async()`
- `SearchCrew` handles a single MP per execution
- `DateFilteredSerperTool` filters results to past 8 months via Serper `tbs=qdr:m8` parameter
- Results aggregated into `search_results.json`

**Phase 2: Sequential Analysis** (`crew.py`)
1. `content_filter` (gpt-4o-mini) - Filters/scores results, keeps score 6+
2. `context_researcher` (gpt-4o-mini) - Adds political background
3. `summary_composer` (claude-sonnet-4-5) - Creates strategic markdown report
4. `email_distributor` (gpt-4o-mini) - Sends via SendGrid

### Key Files

```
src/mp_news_feed/
├── main.py              # Entry point, orchestrates both phases
├── search_service.py    # Async search orchestration
├── search_crew.py       # Single-MP search crew
├── crew.py              # Analysis pipeline crew + Pydantic models
├── config/
│   ├── agents.yaml      # Agent roles, goals, LLM assignments
│   ├── tasks.yaml       # Analysis task definitions
│   └── search_tasks.yaml # Search task definition
└── tools/
    ├── date_filtered_serper.py  # Custom Serper with time filtering
    └── sendgrid_tool.py         # Email distribution
```

### Output Pipeline

Tasks write to `output/` sequentially:
1. `search_results.json` → raw articles from Phase 1
2. `filtered_news_items.json` → scored items (6+)
3. `contextualized_news.json` → items with political context
4. `summary_report.md` → final strategic report

### Pydantic Models (crew.py)

- `MpNewsResearch` / `MpNewsResearchList` - Search results
- `ContentFilteredItem` / `ContentFilteredList` - Filtered with scores
- `NewsContextItem` / `NewsContextList` - Contextualized news
- `MPSearchResult` / `ArticleResult` (search_crew.py) - Single MP results

## Environment Variables

```
OPENAI_API_KEY    # Required - gpt-4o-mini calls
ANTHROPIC_API_KEY # Required - summary_composer uses Claude
SERPER_API_KEY    # Required - web searches
SENDGRID_API_KEY  # Required - email distribution
```

## Configuration

- `knowledge/mp_list.json` - MPs to monitor (name + country fields)
- `config/agents.yaml` - Agent LLM assignments
- `main.py:57` - `max_concurrency` for parallel search (default: 10)
- `tools/date_filtered_serper.py` - `months_back` for time filtering

## Rate Limit Considerations

- OpenAI gpt-4o-mini: 200K TPM - handles high concurrency well
- Anthropic Claude: 50K TPM - only used for summary_composer (small input ~2K tokens)
- Serper: Controlled via `max_rpm` in search_service.py
