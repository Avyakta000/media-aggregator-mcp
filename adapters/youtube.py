from __future__ import annotations

import logging
from typing import List, Optional

from core.config import settings
from core.models import MediaItem
from core.utils import http_get_json, make_stable_id, normalize_log_scale, safe_parse_datetime


logger = logging.getLogger("MediaAggregatorMCP")


def fetch_youtube_trends(
    *, topic: Optional[str] = None, region: Optional[str] = None, limit: int = 20
) -> List[MediaItem]:
    """Fetch trending videos from YouTube Data API v3.

    Requires `YOUTUBE_API_KEY` in environment. Falls back to empty list if missing.
    """
    if not settings.youtube_api_key:
        logger.info("Skipping YouTube fetch: missing youtube_api_key")
        return []

    region_code = (region or settings.default_region)
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": max(min(limit, 50), 1),
        "key": settings.youtube_api_key,
    }
    data = http_get_json(url, params=params)
    items = []
    for entry in data.get("items", []):
        video_id = entry.get("id")
        snippet = entry.get("snippet", {})
        statistics = entry.get("statistics", {})
        title = snippet.get("title") or ""
        description = snippet.get("description")
        published_at = safe_parse_datetime(snippet.get("publishedAt"))
        view_count = float(statistics.get("viewCount", 0))
        like_count = float(statistics.get("likeCount", 0)) if statistics.get("likeCount") else 0.0

        popularity = normalize_log_scale(view_count) + 0.1 * normalize_log_scale(like_count)

        items.append(
            MediaItem(
                id=f"yt_{video_id}",
                title=title,
                source="youtube",
                url=f"https://www.youtube.com/watch?v={video_id}",
                description=description,
                published_at=published_at,
                region=region_code,
                topic=topic,
                metrics={"views": view_count, "likes": like_count},
                popularity_score=popularity,
                tags=["video", "youtube"],
            )
        )
    return items


