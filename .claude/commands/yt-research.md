# YouTube Research Skill

Search YouTube for videos on a given topic and return rich metadata including title, views, author, duration, and URL.

## Usage

When the user invokes `/yt-research`, follow these steps:

1. **Check for a topic**: If the user has not specified a topic, ask: "What topic would you like me to research on YouTube?"

2. **Parse parameters** from the user's message:
   - `topic` — the search query (required; ask if missing)
   - `count` — number of videos to fetch (default: 25)

3. **Run the research script**:
   ```bash
   python3 skills/yt_research.py "<topic>" -n <count> --format json
   ```

4. **Present results** as a formatted table showing rank, title, author, duration, views, and URL.

5. **Offer next steps**: Ask the user if they want to send these videos to NotebookLM for analysis using `/notebooklm`.

## Examples

- `/yt-research AI agents 2025` — find 25 videos about AI agents
- `/yt-research "machine learning tutorials" -n 10` — find top 10 ML tutorial videos

## Notes

- Uses `yt-dlp` under the hood (no API key required)
- Results are sorted by YouTube's default relevance/trending ranking
- If yt-dlp is not installed, it will prompt to run: `pip install yt-dlp`
