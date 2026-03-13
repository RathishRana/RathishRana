#!/usr/bin/env python3
"""
YouTube Research Skill
Scrapes YouTube metadata (title, views, author, duration, URL) using yt-dlp.
"""

import sys
import json
import argparse

try:
    import yt_dlp
except ImportError:
    print(json.dumps({"error": "yt-dlp is not installed. Run: pip install yt-dlp"}))
    sys.exit(1)


def search_youtube(query: str, max_results: int = 25) -> list[dict]:
    """Search YouTube and return video metadata."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "default_search": f"ytsearch{max_results}",
        "skip_download": True,
    }

    results = []
    search_url = f"ytsearch{max_results}:{query}"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        if not info or "entries" not in info:
            return results

        for entry in info["entries"]:
            if not entry:
                continue

            video_id = entry.get("id", "")
            url = f"https://www.youtube.com/watch?v={video_id}" if video_id else entry.get("url", "")

            # Format duration as mm:ss or hh:mm:ss
            duration_secs = entry.get("duration")
            if duration_secs:
                h = int(duration_secs) // 3600
                m = (int(duration_secs) % 3600) // 60
                s = int(duration_secs) % 60
                duration_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            else:
                duration_str = "N/A"

            # Format view count
            view_count = entry.get("view_count")
            if view_count is not None:
                if view_count >= 1_000_000:
                    views_str = f"{view_count / 1_000_000:.1f}M"
                elif view_count >= 1_000:
                    views_str = f"{view_count / 1_000:.1f}K"
                else:
                    views_str = str(view_count)
            else:
                views_str = "N/A"

            results.append({
                "rank": len(results) + 1,
                "title": entry.get("title", "Unknown Title"),
                "author": entry.get("uploader") or entry.get("channel") or "Unknown",
                "duration": duration_str,
                "views": views_str,
                "view_count_raw": view_count or 0,
                "upload_date": entry.get("upload_date", "N/A"),
                "url": url,
            })

    return results


def format_table(videos: list[dict]) -> str:
    """Format video list as a readable text table."""
    if not videos:
        return "No results found."

    lines = [
        f"{'#':<4} {'Title':<55} {'Author':<25} {'Duration':<10} {'Views':<10} URL",
        "-" * 130,
    ]
    for v in videos:
        title = v["title"][:52] + "..." if len(v["title"]) > 55 else v["title"]
        author = v["author"][:22] + "..." if len(v["author"]) > 25 else v["author"]
        lines.append(
            f"{v['rank']:<4} {title:<55} {author:<25} {v['duration']:<10} {v['views']:<10} {v['url']}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search YouTube and return video metadata.")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("-n", "--max-results", type=int, default=25,
                        help="Number of results to return (default: 25)")
    parser.add_argument("--format", choices=["json", "table"], default="json",
                        help="Output format: json (default) or table")
    args = parser.parse_args()

    videos = search_youtube(args.query, args.max_results)

    if args.format == "table":
        print(format_table(videos))
    else:
        print(json.dumps({"query": args.query, "count": len(videos), "videos": videos}, indent=2))


if __name__ == "__main__":
    main()
