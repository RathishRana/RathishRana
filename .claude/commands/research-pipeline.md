# Automated YouTube → NotebookLM Research Pipeline

Run the full research pipeline: scrape YouTube videos on a topic, feed them into NotebookLM, get an analysis, and generate a deliverable.

## Trigger

Use this skill when the user asks to research a topic and deliver findings via NotebookLM. Example commands:
- "Use the yt-research skill to find the 25 latest trending videos on [TOPIC]..."
- "Research [TOPIC] on YouTube and create a NotebookLM infographic"

## Step-by-Step Execution

### Step 0 — Check for Topic
If no topic is specified, **stop and ask**:
> "What topic would you like me to research? Please provide a topic before I proceed."

Do not continue until the topic is confirmed.

### Step 1 — YouTube Research
Run the YouTube research script and collect video metadata:

```bash
python3 skills/yt_research.py "<TOPIC>" -n <COUNT> --format json
```

- Default `COUNT` = 25 unless the user specifies otherwise
- Parse the JSON output to get the list of video URLs
- Present a summary table to the user (title, author, views, duration, URL)

### Step 2 — Create NotebookLM Notebook
Create a new notebook with a descriptive title:

```bash
python3 skills/notebooklm_skill.py create "YouTube Research: <TOPIC>"
```

Save the returned `notebook_id` for subsequent steps.

### Step 3 — Upload YouTube Sources
Add all video URLs from Step 1 as sources. Batch them efficiently:

```bash
python3 skills/notebooklm_skill.py add-sources "<notebook_id>" <url1> <url2> ... <urlN>
```

Report how many sources were successfully added.

### Step 4 — Request Analysis
Ask NotebookLM for its key findings:

```bash
python3 skills/notebooklm_skill.py ask "<notebook_id>" "Analyze these YouTube videos about <TOPIC>. What are the top trends, key themes, most important insights, and notable patterns? Provide a structured summary of the top findings."
```

Present the analysis to the user.

### Step 5 — Generate Deliverable
Based on the user's request, generate the appropriate deliverable. For infographics with a style:

```bash
python3 skills/notebooklm_skill.py generate "<notebook_id>" infographic \
  --orientation portrait \
  --style "<style instructions from user, e.g. handwritten chalkboard>"
```

Supported deliverables: `infographic`, `slideshow`, `flashcards`, `audio`, `quiz`

### Step 6 — Download & Report
Download the deliverable if applicable:

```bash
python3 skills/notebooklm_skill.py download "<notebook_id>" infographic "./output/<topic>_infographic.png"
```

Report the output path and summarize what was accomplished.

## Authentication Check

If NotebookLM commands fail with an authentication error, remind the user:

> **Authentication Required**: Please open a separate terminal and run:
> ```bash
> notebooklm login
> ```
> This will open a browser for Google sign-in. Once complete, re-run the pipeline.

## Error Handling

- If `yt-dlp` is missing: `pip install yt-dlp`
- If `notebooklm-py` is missing: `pip install 'notebooklm-py[browser]' && playwright install chromium`
- If source upload fails for some URLs: continue with successfully added URLs and report failures
- If deliverable generation is slow: inform the user it may take 1-2 minutes

## Example Full Invocation

User: "Use the yt-research skill to find the 25 latest trending videos on quantum computing. Once we have those videos, send them over to NotebookLM. Give me its analysis on the top findings, then have NotebookLM create an infographic in a handwritten / chalkboard style depicting that analysis."

→ Execute Steps 1–6 above with TOPIC="quantum computing", COUNT=25, DELIVERABLE=infographic, STYLE="handwritten chalkboard style"
