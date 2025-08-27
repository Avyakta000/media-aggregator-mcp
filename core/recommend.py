from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.aggregator import SUPPORTED_SOURCES, fetch_trends
from core.config import settings
from core.models import MediaItem, Recommendation, ScoreBreakdown
from core.utils import clamp, text_contains_any


logger = logging.getLogger("MediaAggregatorMCP")


def list_supported_sources() -> List[str]:
    return list(SUPPORTED_SOURCES.keys())


def _score_item_for_recommendation(item: MediaItem, topic: str, user_prefs: Dict[str, Any]) -> Recommendation:
    preferred_sources = set([s.lower() for s in user_prefs.get("preferred_sources", [])])
    keywords = [kw for kw in user_prefs.get("keywords", []) if isinstance(kw, str)]

    breakdown = ScoreBreakdown()

    # Base score from adapter
    base = item.popularity_score

    # Source weight
    if preferred_sources:
        breakdown.source_weight = 0.2 if item.source.lower() in preferred_sources else 0.0

    # Topic match
    title_desc = f"{item.title}\n{item.description or ''}"
    if topic and text_contains_any(title_desc, [topic]):
        breakdown.topic_match_boost = 0.25

    # Keyword match
    if keywords and text_contains_any(title_desc, keywords):
        breakdown.user_pref_boost = 0.2

    # Recency and engagement approximations embedded in base
    breakdown.engagement_score = clamp(base / 100.0, 0.0, 0.5)
    breakdown.recency_boost = 0.1 if item.published_at else 0.0

    total = base + sum([
        breakdown.source_weight,
        breakdown.topic_match_boost,
        breakdown.user_pref_boost,
        breakdown.engagement_score,
        breakdown.recency_boost,
    ])
    breakdown.total = total
    return Recommendation(item=item, score=total, breakdown=breakdown)


def generate_recommendations(
    *,
    topic: str,
    user_prefs: Dict[str, Any],
    region: Optional[str],
    limit: int,
) -> List[Recommendation]:
    """Return recommendations for a topic using simple but transparent scoring."""
    items: List[MediaItem] = fetch_trends(topic=topic, region=region, limit=max(limit, settings.default_limit))
    recs = [_score_item_for_recommendation(item, topic, user_prefs) for item in items]
    recs.sort(key=lambda r: r.score, reverse=True)
    return recs[:limit]


def explain_ranking(item_id: str) -> Dict[str, Any]:
    """Provide best-effort explanation for a given item id.

    This implementation is stateless and derives an explanation hint from the id
    pattern. A production version would look up from a cache of the last
    recommendation request context.
    """
    # A minimal placeholder since we don't persist sessions here.
    source_hint = "youtube" if item_id.startswith("yt_") else (
        "reddit" if item_id.startswith("rd_") else (
            "newsapi" if item_id.startswith("nw_") else (
                "google_trends" if item_id.startswith("gt_") else "unknown"
            )
        )
    )
    return {
        "item_id": item_id,
        "explanation": "Ranking is based on source popularity score, topic match, and user preference boosts.",
        "source_hint": source_hint,
        "factors": [
            "Base popularity score from the source",
            "Topic and keyword match boosts",
            "Light recency and engagement normalization",
        ],
    }


