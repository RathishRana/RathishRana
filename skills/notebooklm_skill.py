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
    from notebooklm.rpc.types import InfographicOrientation, InfographicStyle, SlideDeckFormat
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
    # Map orientation string to enum
    orient_map = {
        "portrait": InfographicOrientation.PORTRAIT,
        "landscape": InfographicOrientation.LANDSCAPE,
        "square": InfographicOrientation.SQUARE,
    }
    orient_enum = orient_map.get(orientation.lower(), InfographicOrientation.PORTRAIT)

    async with await NotebookLMClient.from_storage() as client:
        if deliverable_type == "infographic":
            status = await client.artifacts.generate_infographic(
                notebook_id,
                orientation=orient_enum,
                style=InfographicStyle.SKETCH_NOTE,
                instructions=style_note or None,
            )
        elif deliverable_type == "slideshow":
            status = await client.artifacts.generate_slide_deck(
                notebook_id,
                instructions=style_note or None,
            )
        elif deliverable_type == "flashcards":
            status = await client.artifacts.generate_flashcards(notebook_id)
        elif deliverable_type == "audio":
            status = await client.artifacts.generate_audio(notebook_id)
        elif deliverable_type == "quiz":
            status = await client.artifacts.generate_quiz(notebook_id)
        else:
            return {"error": f"Unknown deliverable type: {deliverable_type}"}

        # Wait for generation to complete
        print(f"Waiting for {deliverable_type} generation (task_id={status.task_id})...", flush=True)
        artifact = await client.artifacts.wait_for_completion(notebook_id, status.task_id)

        return {
            "notebook_id": notebook_id,
            "deliverable_type": deliverable_type,
            "status": "generated",
            "artifact_id": getattr(artifact, "id", None),
            "task_id": status.task_id,
        }


async def download_deliverable(notebook_id: str, deliverable_type: str, output_path: str) -> dict:
    async with await NotebookLMClient.from_storage() as client:
        if deliverable_type == "infographic":
            saved = await client.artifacts.download_infographic(notebook_id, output_path)
        elif deliverable_type == "slideshow":
            saved = await client.artifacts.download_slide_deck(notebook_id, output_path)
        elif deliverable_type == "audio":
            saved = await client.artifacts.download_audio(notebook_id, output_path)
        else:
            return {"error": f"Download not supported for: {deliverable_type}"}
        return {"status": "downloaded", "path": saved}


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
                status = await client.artifacts.generate_infographic(
                    notebook_id,
                    orientation=InfographicOrientation.PORTRAIT,
                    style=InfographicStyle.SKETCH_NOTE,
                    instructions=deliverable_style or None,
                )
                deliverable_result = await client.artifacts.wait_for_completion(notebook_id, status.task_id)
            elif deliverable_type == "slideshow":
                status = await client.artifacts.generate_slide_deck(
                    notebook_id,
                    instructions=deliverable_style or None,
                )
                deliverable_result = await client.artifacts.wait_for_completion(notebook_id, status.task_id)
            elif deliverable_type == "flashcards":
                status = await client.artifacts.generate_flashcards(notebook_id)
                deliverable_result = await client.artifacts.wait_for_completion(notebook_id, status.task_id)
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
