# NotebookLM Skill

Interact with Google NotebookLM to create notebooks, upload YouTube sources, request analysis, and generate deliverables (infographics, slide decks, flashcards, etc.).

## Authentication Reminder

Before using this skill, ensure you have authenticated. Open a **separate terminal** and run:
```bash
notebooklm login
```
This opens a browser window for Google account sign-in.

## Usage

When the user invokes `/notebooklm`, interpret their intent and call the appropriate sub-command:

### Create a Notebook
```bash
python3 skills/notebooklm_skill.py create "<notebook title>"
```

### Add YouTube (or any URL) Sources
```bash
python3 skills/notebooklm_skill.py add-sources "<notebook_id>" "<url1>" "<url2>" ...
```

### Ask for Analysis
```bash
python3 skills/notebooklm_skill.py ask "<notebook_id>" "<question>"
```

### Generate a Deliverable
```bash
python3 skills/notebooklm_skill.py generate "<notebook_id>" infographic --style "handwritten chalkboard style"
python3 skills/notebooklm_skill.py generate "<notebook_id>" slideshow
python3 skills/notebooklm_skill.py generate "<notebook_id>" flashcards
```

### Download a Deliverable
```bash
python3 skills/notebooklm_skill.py download "<notebook_id>" infographic "./output/infographic.png"
```

### Full Pipeline (one command)
```bash
python3 skills/notebooklm_skill.py pipeline \
  --title "<notebook title>" \
  --urls "<url1>" "<url2>" \
  --question "<analysis question>" \
  --deliverable infographic \
  --style "<style note e.g. handwritten chalkboard>" \
  --output "./output/result.png"
```

## Deliverable Types

| Type         | Description                              |
|--------------|------------------------------------------|
| `infographic`| Visual summary (portrait or landscape)   |
| `slideshow`  | Presentation slide deck                  |
| `flashcards` | Study flashcards                         |
| `audio`      | Audio overview / podcast                 |
| `quiz`       | Interactive quiz                         |

## Notes

- Requires `notebooklm-py[browser]` installed and `playwright install chromium` run
- Authentication must be completed first via `notebooklm login`
- Notebook IDs are returned when you create a notebook — keep track of them
