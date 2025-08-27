from __future__ import annotations

import logging
from typing import List, Optional

import praw

from core.config import settings
from core.models import MediaItem
from core.utils import make_stable_id, normalize_log_scale, safe_parse_datetime


logger = logging.getLogger("MediaAggregatorMCP")


def _get_reddit_client() -> Optional[praw.Reddit]:
    if not (settings.reddit_client_id and settings.reddit_client_secret and settings.reddit_user_agent):
        return None
    try:
        return praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
    except Exception as exc:
        logger.warning("Failed to init Reddit client: %s", exc)
        return None


def fetch_reddit_trends(
    *, topic: Optional[str] = None, region: Optional[str] = None, limit: int = 20
) -> List[MediaItem]:
    """Fetch hot posts from Reddit related to topic or from r/all."""
    reddit = _get_reddit_client()
    if reddit is None:
        logger.info("Skipping Reddit fetch: missing credentials")
        return []

    items: List[MediaItem] = []
    try:
        subreddit = reddit.subreddit("all" if not topic else topic)
        for idx, submission in enumerate(subreddit.hot(limit=limit)):
            score = float(getattr(submission, "score", 0) or 0)
            comments = float(getattr(submission, "num_comments", 0) or 0)
            popularity = normalize_log_scale(score) + 0.1 * normalize_log_scale(comments)
            items.append(
                MediaItem(
                    id=f"rd_{submission.id}",
                    title=submission.title or "",
                    source="reddit",
                    url=submission.url or f"https://reddit.com{submission.permalink}",
                    description=getattr(submission, "selftext", None) or None,
                    published_at=None,
                    region=region,
                    topic=topic,
                    metrics={"score": score, "comments": comments},
                    popularity_score=popularity,
                    tags=["reddit", "post"],
                )
            )
    except Exception as exc:
        logger.warning("Failed to fetch Reddit trends: %s", exc)
        return []
    return items


