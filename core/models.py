from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl


SourceName = Literal["youtube", "reddit", "newsapi"]


class MediaItem(BaseModel):
    """Canonical representation of a media/trend item across sources."""

    id: str
    title: str
    source: SourceName
    url: Union[str, HttpUrl]

    description: Optional[str] = None
    published_at: Optional[datetime] = None
    region: Optional[str] = None
    topic: Optional[str] = None

    metrics: Dict[str, Union[int, float, str]] = Field(default_factory=dict)
    popularity_score: float = 0.0
    tags: List[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """Transparent scoring components used for recommendations and trends."""

    source_weight: float = 0.0
    recency_boost: float = 0.0
    engagement_score: float = 0.0
    topic_match_boost: float = 0.0
    user_pref_boost: float = 0.0
    total: float = 0.0


class Recommendation(BaseModel):
    """A recommendation with its score and breakdown for explainability."""

    item: MediaItem
    score: float
    breakdown: ScoreBreakdown


