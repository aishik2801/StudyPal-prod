"""
YouTube recommendation engine — searches for relevant learning videos.
Uses direct HTTP requests to avoid youtubesearchpython compatibility issues.
"""

from __future__ import annotations

import re
import json
import urllib.parse
from typing import List, Dict

import httpx

from core.constants import YOUTUBE_MAX_RESULTS


def search_youtube(
    query: str,
    max_results: int | None = None,
) -> List[Dict[str, str]]:
    """
    Search YouTube for educational videos matching ``query``.

    Args:
        query: Topic or question to search for.
        max_results: Number of results to return.

    Returns:
        List of dicts with keys: title, url, thumbnail, duration, channel.
    """
    max_results = max_results or YOUTUBE_MAX_RESULTS
    search_query = urllib.parse.quote(f"{query} tutorial explanation")
    url = f"https://www.youtube.com/results?search_query={search_query}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = httpx.get(url, headers=headers, timeout=10, follow_redirects=True)
    response.raise_for_status()
    html = response.text

    # Extract the ytInitialData JSON from the page
    pattern = r"var ytInitialData\s*=\s*({.*?});"
    match = re.search(pattern, html, re.DOTALL)
    if not match:
        # Fallback pattern
        pattern = r"ytInitialData\s*=\s*({.*?});"
        match = re.search(pattern, html, re.DOTALL)

    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    videos: List[Dict[str, str]] = []

    try:
        contents = (
            data["contents"]["twoColumnSearchResultsRenderer"]
            ["primaryContents"]["sectionListRenderer"]
            ["contents"][0]["itemSectionRenderer"]["contents"]
        )
    except (KeyError, IndexError):
        return []

    for item in contents:
        if "videoRenderer" not in item:
            continue
        renderer = item["videoRenderer"]

        video_id = renderer.get("videoId", "")
        title_runs = renderer.get("title", {}).get("runs", [])
        title = title_runs[0].get("text", "") if title_runs else ""

        # Duration
        duration_text = renderer.get("lengthText", {}).get("simpleText", "")

        # Channel
        channel_runs = renderer.get("ownerText", {}).get("runs", [])
        channel = channel_runs[0].get("text", "") if channel_runs else ""

        # Thumbnail
        thumbs = renderer.get("thumbnail", {}).get("thumbnails", [])
        thumb_url = thumbs[-1].get("url", "") if thumbs else ""

        if video_id and title:
            videos.append(
                {
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": thumb_url,
                    "duration": duration_text,
                    "channel": channel,
                }
            )

        if len(videos) >= max_results:
            break

    return videos
