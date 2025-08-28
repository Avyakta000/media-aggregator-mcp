import logging
import contextlib
from typing import Any, Dict, List, Optional, Literal

from fastmcp import FastMCP

from core.aggregator import fetch_trends, fetch_trends_by_source
from core.config import settings
from core.recommend import explain_ranking, generate_recommendations, list_supported_sources
from adapters.transcript import TranscriptError, fetch_youtube_transcript
from fastmcp.server.auth.providers.workos import AuthKitProvider
from starlette.applications import Starlette
from starlette.routing import Mount

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("MediaAggregatorMCP")


auth = AuthKitProvider(
    authkit_domain=settings.authkit_domain,
    base_url=settings.base_url
)
mcp = FastMCP(settings.mcp_server_name, auth=auth)


@mcp.tool()
def get_trends_by_source(
    source: Literal["youtube", "reddit", "newsapi"],
    topic: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Fetch trends from a specific source."""
    items = fetch_trends_by_source(source=source, topic=topic, region=region, limit=limit)
    return [item.model_dump(mode="json") for item in items]


@mcp.tool()
def recommend(
    topic: str,
    user_prefs: Optional[Dict[str, Any]] = None,
    region: Optional[str] = None,
    limit: int = 10,
    source: Optional[Literal["youtube", "reddit", "newsapi"]] = None,
) -> List[Dict[str, Any]]:
    """Return recommendations based on current trends."""
    prefs = user_prefs or {}
    if source:
        # Bias recommendations toward the provided source
        preferred = set(prefs.get("preferred_sources", []))
        preferred.add(source)
        prefs["preferred_sources"] = list(preferred)

    recommendations = generate_recommendations(
        topic=topic, user_prefs=prefs, region=region, limit=limit
    )
    return [
        {
            "item": rec.item.model_dump(mode="json"),
            "score": rec.score,
            "breakdown": rec.breakdown.model_dump(mode="json"),
        }
        for rec in recommendations
    ]


@mcp.tool()
def explain(item_id: str) -> Dict[str, Any]:
    """Explain why an item is ranked the way it is."""
    return explain_ranking(item_id)


@mcp.tool()
def transcribe_youtube(
    video_url: str,
    language: str = "en",
    transcript_type: str = "auto",
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """Transcribe a YouTube video using the YouTube Transcript API.
    (Optional) The transcript type can be one of the following:
        - "manual" - use the manually created transcript
        - "generated" - use the generated transcript
        - "auto" - it will attempt to use the manually created transcript first, then fallback to generated
    """
    if transcript_type not in ["manual", "generated", "auto"]:
        raise ValueError(f"Invalid transcript type: {transcript_type}. Must be one of: manual, generated, auto")
    try:
        return fetch_youtube_transcript(
            video_url=video_url,
            language=language,
            transcript_type=transcript_type,
            include_metadata=include_metadata
        )
    except TranscriptError as exc:
        return {"error": str(exc)}


# ---------------- Resources ----------------
@mcp.resource("media-aggregator://sources")
def sources_resource() -> Dict[str, Any]:
    return {"sources": list_supported_sources(), "default_region": settings.default_region}


@mcp.resource("media-aggregator://status", mime_type="application/json")
def status_resource() -> Dict[str, Any]:
    return {"name": settings.mcp_server_name, "status": "ok"}


@mcp.resource("media-aggregator://trends/{topic}", mime_type="application/json")
def resource_trends(
    topic: str,
    region: Optional[str] = None,
    limit: int = 20,
    source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Resource template returning unified trends for a topic."""
    if source:
        items = fetch_trends_by_source(source=source, topic=topic, region=region, limit=limit)
    else:
        items = fetch_trends(topic=topic, region=region, limit=limit)
    return [item.model_dump(mode="json") for item in items]


@mcp.resource("media-aggregator://source/{source}/{topic}", mime_type="application/json")
def resource_trends_by_source(source: str, topic: str, region: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Resource template returning per-source trends for a topic."""
    items = fetch_trends_by_source(source=source, topic=topic, region=region, limit=limit)
    return [item.model_dump(mode="json") for item in items]


@mcp.resource("media-aggregator://recommend/{topic}", mime_type="application/json")
def resource_recommend(topic: str, region: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Resource template returning recommendations for a topic."""
    recs = generate_recommendations(topic=topic, user_prefs={}, region=region, limit=limit)
    return [
        {
            "item": rec.item.model_dump(mode="json"),
            "score": rec.score,
            "breakdown": rec.breakdown.model_dump(mode="json"),
        }
        for rec in recs
    ]


@mcp.prompt
def summarize_trends(topic: str, region: Optional[str] = None) -> str:
    r = region or settings.default_region
    return f"Summarize key takeaways for current '{topic}' trends in {r}."


@mcp.prompt
def explain_recommendation(item_id: str) -> str:
    return (
     f"Explain why the item with id '" + item_id + "' ranks highly, "
     "considering source popularity, topic match, engagement, and recency."
    )


mcp_app = mcp.http_app(path='/mcp')

app = Starlette(
    routes=[
        Mount("/", app=mcp_app),
    ],
    lifespan=mcp_app.lifespan,
)
