#!/usr/bin/env python3
"""
NotebookLM Skill
Interacts with NotebookLM via the unofficial notebooklm-py API.
Supports: create notebook, add YouTube sources, request analysis & deliverables.
"""

import sys
import json
import argparse
import asyncio

try:
    from notebooklm import NotebookLMClient
except ImportError:
    print(json.dumps({
        "error": (
            "notebooklm-py is not installed. Run:\n"
            "  pip install 'notebooklm-py[browser]'\n"
            "  playwright install chromium\n"
            "Then authenticate with:\n"
            "  notebooklm login"
        )
    }))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Core async helpers
# ---------------------------------------------------------------------------

async def create_notebook(title: str) -> dict:
    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create(title)
        return {"notebook_id": nb.id, "title": nb.title, "status": "created"}


async def add_sources(notebook_id: str, urls: list[str]) -> dict:
    results = []
    async with await NotebookLMClient.from_storage() as client:
        for url in urls:
            try:
                await client.sources.add_url(notebook_id, url)
                results.append({"url": url, "status": "added"})
            except Exception as e:
                results.append({"url": url, "status": "error", "message": str(e)})
    return {"notebook_id": notebook_id, "sources": results}


async def ask_notebook(notebook_id: str, question: str) -> dict:
    async with await NotebookLMClient.from_storage() as client:
        result = await client.chat.ask(notebook_id, question)
        return {
            "notebook_id": notebook_id,
            "question": question,
            "answer": result.answer,
        }


async def generate_deliverable(
    notebook_id: str,
    deliverable_type: str,
    orientation: str = "portrait",
    style_note: str = "",
) -> dict:
    """
    Request a deliverable from NotebookLM.
    deliverable_type: infographic | slideshow | flashcards | audio | video | quiz
    """
    async with await NotebookLMClient.from_storage() as client:
        prompt_extra = f" Style: {style_note}" if style_note else ""

        if deliverable_type == "infographic":
            result = await client.generate.infographic(
                notebook_id,
                orientation=orientation,
                additional_instructions=prompt_extra.strip(),
            )
        elif deliverable_type == "slideshow":
            result = await client.generate.slideshow(
                notebook_id,
                additional_instructions=prompt_extra.strip(),
            )
        elif deliverable_type == "flashcards":
            result = await client.generate.flashcards(notebook_id)
        elif deliverable_type == "audio":
            result = await client.generate.audio(notebook_id)
        elif deliverable_type == "quiz":
            result = await client.generate.quiz(notebook_id)
        else:
            return {"error": f"Unknown deliverable type: {deliverable_type}"}

        return {
            "notebook_id": notebook_id,
            "deliverable_type": deliverable_type,
            "status": "generated",
            "result_id": getattr(result, "id", None),
            "download_url": getattr(result, "download_url", None),
            "data": getattr(result, "data", None),
        }


async def download_deliverable(notebook_id: str, deliverable_type: str, output_path: str) -> dict:
    async with await NotebookLMClient.from_storage() as client:
        if deliverable_type == "infographic":
            await client.download.infographic(notebook_id, output_path)
        elif deliverable_type == "slideshow":
            await client.download.slideshow(notebook_id, output_path)
        elif deliverable_type == "audio":
            await client.download.audio(notebook_id, output_path)
        else:
            return {"error": f"Download not supported for: {deliverable_type}"}
        return {"status": "downloaded", "path": output_path}


async def full_pipeline(
    notebook_title: str,
    urls: list[str],
    analysis_question: str,
    deliverable_type: str,
    deliverable_style: str = "",
    output_path: str = "./deliverable_output.png",
) -> dict:
    """
    End-to-end pipeline:
    1. Create notebook
    2. Add URL sources
    3. Get analysis
    4. Generate deliverable
    5. Download deliverable
    """
    async with await NotebookLMClient.from_storage() as client:
        # 1. Create notebook
        nb = await client.notebooks.create(notebook_title)
        notebook_id = nb.id

        # 2. Add sources
        source_results = []
        for url in urls:
            try:
                await client.sources.add_url(notebook_id, url)
                source_results.append({"url": url, "status": "added"})
            except Exception as e:
                source_results.append({"url": url, "status": "error", "message": str(e)})

        # 3. Analysis
        analysis_result = await client.chat.ask(notebook_id, analysis_question)

        # 4. Generate deliverable
        deliverable_result = None
        try:
            if deliverable_type == "infographic":
                deliverable_result = await client.generate.infographic(
                    notebook_id,
                    additional_instructions=deliverable_style,
                )
            elif deliverable_type == "slideshow":
                deliverable_result = await client.generate.slideshow(
                    notebook_id,
                    additional_instructions=deliverable_style,
                )
            elif deliverable_type == "flashcards":
                deliverable_result = await client.generate.flashcards(notebook_id)
        except Exception as e:
            deliverable_result = {"error": str(e)}

        return {
            "notebook_id": notebook_id,
            "notebook_title": notebook_title,
            "sources_added": len([s for s in source_results if s["status"] == "added"]),
            "sources_failed": len([s for s in source_results if s["status"] == "error"]),
            "source_details": source_results,
            "analysis": analysis_result.answer,
            "deliverable_type": deliverable_type,
            "deliverable_style": deliverable_style,
            "deliverable_status": "generated" if deliverable_result else "skipped",
        }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="NotebookLM Skill CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create a new notebook")
    p_create.add_argument("title", help="Notebook title")

    # add-sources
    p_add = subparsers.add_parser("add-sources", help="Add URL sources to a notebook")
    p_add.add_argument("notebook_id", help="Notebook ID")
    p_add.add_argument("urls", nargs="+", help="URLs to add as sources")

    # ask
    p_ask = subparsers.add_parser("ask", help="Ask a question against a notebook")
    p_ask.add_argument("notebook_id", help="Notebook ID")
    p_ask.add_argument("question", help="Question to ask")

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate a deliverable")
    p_gen.add_argument("notebook_id", help="Notebook ID")
    p_gen.add_argument("type", choices=["infographic", "slideshow", "flashcards", "audio", "quiz"],
                       help="Deliverable type")
    p_gen.add_argument("--orientation", default="portrait", help="Orientation (portrait/landscape)")
    p_gen.add_argument("--style", default="", help="Style note for the deliverable")

    # download
    p_dl = subparsers.add_parser("download", help="Download a generated deliverable")
    p_dl.add_argument("notebook_id", help="Notebook ID")
    p_dl.add_argument("type", help="Deliverable type")
    p_dl.add_argument("output", help="Output file path")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="Run full research pipeline")
    p_pipe.add_argument("--title", required=True, help="Notebook title")
    p_pipe.add_argument("--urls", nargs="+", required=True, help="Source URLs")
    p_pipe.add_argument("--question", required=True, help="Analysis question")
    p_pipe.add_argument("--deliverable", default="infographic",
                        choices=["infographic", "slideshow", "flashcards", "none"])
    p_pipe.add_argument("--style", default="", help="Deliverable style instructions")
    p_pipe.add_argument("--output", default="./deliverable_output.png", help="Output path")

    args = parser.parse_args()

    if args.command == "create":
        result = asyncio.run(create_notebook(args.title))
    elif args.command == "add-sources":
        result = asyncio.run(add_sources(args.notebook_id, args.urls))
    elif args.command == "ask":
        result = asyncio.run(ask_notebook(args.notebook_id, args.question))
    elif args.command == "generate":
        result = asyncio.run(generate_deliverable(
            args.notebook_id, args.type, args.orientation, args.style
        ))
    elif args.command == "download":
        result = asyncio.run(download_deliverable(args.notebook_id, args.type, args.output))
    elif args.command == "pipeline":
        result = asyncio.run(full_pipeline(
            args.title, args.urls, args.question, args.deliverable,
            args.style, args.output
        ))
    else:
        result = {"error": f"Unknown command: {args.command}"}

    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
