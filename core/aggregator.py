from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from core.models import MediaItem
from core.utils import clamp

from adapters.newsapi import fetch_newsapi_trends
from adapters.reddit import fetch_reddit_trends
from adapters.youtube import fetch_youtube_trends


logger = logging.getLogger("MediaAggregatorMCP")


SUPPORTED_SOURCES = {
    "youtube": fetch_youtube_trends,
    "reddit": fetch_reddit_trends,
    "newsapi": fetch_newsapi_trends,
}


def _sort_and_limit(items: Iterable[MediaItem], limit: int) -> List[MediaItem]:
    sorted_items = sorted(items, key=lambda it: it.popularity_score, reverse=True)
    return list(sorted_items)[: max(limit, 0)]


def fetch_trends(
    topic: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 20,
) -> List[MediaItem]:
    """Aggregate trends from all sources into a unified list of `MediaItem`.

    Items are scored within adapters and combined here. Results are globally
    sorted by `popularity_score` then limited to `limit`.
    """
    all_items: List[MediaItem] = []
    for source, fetcher in SUPPORTED_SOURCES.items():
        try:
            items = fetcher(topic=topic, region=region, limit=limit)
            all_items.extend(items)
        except Exception as exc:
            logger.warning("Failed to fetch trends from %s: %s", source, exc)
            continue
    return _sort_and_limit(all_items, limit)


def fetch_trends_by_source(
    source: str,
    topic: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 20,
) -> List[MediaItem]:
    """Fetch trends from a single source by key name.

    Valid sources: "youtube", "google_trends", "reddit", "newsapi".
    """
    key = source.strip().lower()
    if key not in SUPPORTED_SOURCES:
        raise ValueError(f"Unsupported source '{source}'. Supported: {list(SUPPORTED_SOURCES.keys())}")
    items = SUPPORTED_SOURCES[key](topic=topic, region=region, limit=limit)
    return _sort_and_limit(items, limit)


