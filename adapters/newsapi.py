from __future__ import annotations

import logging
from typing import List, Optional

from core.config import settings
from core.models import MediaItem
from core.utils import http_get_json, make_stable_id, normalize_log_scale, safe_parse_datetime


logger = logging.getLogger("MediaAggregatorMCP")


def fetch_newsapi_trends(
    *, topic: Optional[str] = None, region: Optional[str] = None, limit: int = 20
) -> List[MediaItem]:
    """Fetch top headlines using NewsAPI.org.

    Requires `NEWSAPI_KEY` in environment. Falls back to empty list if missing.
    """
    if not settings.newsapi_key:
        logger.info("Skipping NewsAPI fetch: missing newsapi_key")
        return []

    country = (region or settings.default_region).lower()
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": settings.newsapi_key,
        "pageSize": max(min(limit, 100), 1),
        "country": country if len(country) == 2 else None,
        "q": topic or None,
    }
    # remove None values
    params = {k: v for k, v in params.items() if v is not None}

    try:
        data = http_get_json(url, params=params)
    except Exception as exc:
        logger.warning("Failed NewsAPI request: %s", exc)
        return []

    items: List[MediaItem] = []
    for article in data.get("articles", [])[:limit]:
        title = article.get("title") or ""
        url = article.get("url") or ""
        description = article.get("description")
        published_at = safe_parse_datetime(article.get("publishedAt"))
        source_name = (article.get("source") or {}).get("name") or "news"

        # Approximate popularity by presence of content and source name length
        popularity = 0.3 + 0.05 * len(source_name)
        if description:
            popularity += 0.1

        item_id = make_stable_id("news", title, url)
        items.append(
            MediaItem(
                id=f"nw_{item_id}",
                title=title,
                source="newsapi",
                url=url,
                description=description,
                published_at=published_at,
                region=country,
                topic=topic,
                metrics={},
                popularity_score=popularity,
                tags=["news", "headline"],
            )
        )
    return items


