# RathishRana Research Pipeline

Automated YouTube research and NotebookLM analysis pipeline.

## Custom Skills

| Skill | Command | Description |
|-------|---------|-------------|
| YouTube Research | `/yt-research` | Search YouTube and scrape video metadata (title, views, author, duration, URL) |
| NotebookLM | `/notebooklm` | Create notebooks, add sources, request analysis, generate deliverables |
| Research Pipeline | `/research-pipeline` | Full end-to-end pipeline: YouTube → NotebookLM → Analysis → Deliverable |

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

Authenticate with NotebookLM (run once in a separate terminal):
```bash
notebooklm login
```

## Skill Scripts

- `skills/yt_research.py` — YouTube metadata scraper using yt-dlp
- `skills/notebooklm_skill.py` — NotebookLM API wrapper using notebooklm-py

## Workflow

1. Use `/yt-research <topic>` to find videos
2. Use `/notebooklm` to create a notebook and add sources
3. Or run the full pipeline with `/research-pipeline`

**Important**: If no topic is specified for a research command, always ask the user for a topic before proceeding.
