import logging
import contextlib
from typing import Any, Dict, List, Optional, Literal

from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.middleware import Middleware

from mcpauth import MCPAuth
from mcpauth.config import AuthServerType
from mcpauth.types import ResourceServerConfig, ResourceServerMetadata
from mcpauth.utils import fetch_server_config

from core.aggregator import fetch_trends, fetch_trends_by_source
from core.config import settings
from core.recommend import explain_ranking, generate_recommendations, list_supported_sources
from adapters.transcript import TranscriptError, fetch_youtube_transcript


# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("MediaAggregatorMCP")


# ---------------- MCP Server ----------------
# Note: stateless_http=True enables compatibility with mcpauth
mcp = FastMCP(settings.mcp_server_name, stateless_http=True)


# ---------------- Auth Configuration ----------------
# Replace this with your real issuer (e.g., ScaleKit Nexus, Auth0, Keycloak, etc.)
auth_issuer = "https://surprising-technology-15-staging.authkit.app" # configure in core.config
if not auth_issuer:
    raise ValueError("MCP_AUTH_ISSUER is not set. Please configure your OIDC issuer.")

auth_server_config = fetch_server_config(auth_issuer, AuthServerType.OIDC)
logger.info(f"Loaded Auth server config: {auth_server_config}")

# resource ID for this MCP server
resource_id = f"{settings.base_url}/mcp"

# Protect this MCP server with required scopes
mcp_auth = MCPAuth(
    protected_resources=[
        ResourceServerConfig(
            metadata=ResourceServerMetadata(
                resource=resource_id,
                authorization_servers=[auth_server_config],
                scopes_supported=[
                    "read:trends",
                    "read:recommendations",
                    "read:transcripts",
                ],
            )
        )
    ]
)


# ---------------- Tools ----------------
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


# ---------------- Prompts ----------------
@mcp.prompt
def summarize_trends(topic: str, region: Optional[str] = None) -> str:
    r = region or settings.default_region
    return f"Summarize key takeaways for current '{topic}' trends in {r}."


@mcp.prompt
def explain_recommendation(item_id: str) -> str:
    return f"Explain why the item with id '{item_id}' ranks highly."


# ---------------- Starlette App with Auth ----------------
bearer_auth = Middleware(mcp_auth.bearer_auth_middleware("jwt", resource=resource_id))

# Create the ASGI app
mcp_app = mcp.http_app(path='/mcp')

app = Starlette(
    routes=[
        *mcp_auth.resource_metadata_router().routes,  # exposes .well-known
        Mount("/", app=mcp_app, middleware=[bearer_auth]),
    ],
    lifespan=mcp_app.lifespan,
)


# ---------------- Entrypoint ----------------
# if __name__ == "__main__":
    # import uvicorn
    # logger.info(f"Starting MediaAggregatorMCP with Auth on http://127.0.0.1:8080")
    # uvicorn.run(app, host="0.0.0.0", port=8080)
