from __future__ import annotations

import hashlib
import logging
import math
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import requests
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from core.config import settings


logger = logging.getLogger("MediaAggregatorMCP")


@retry(
    reraise=True,
    stop=stop_after_attempt(settings.request_max_retries),
    wait=wait_exponential(multiplier=max(settings.request_retry_backoff_seconds, 0.1), min=0.1, max=4),
)
def http_get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Perform an HTTP GET returning parsed JSON with basic retries.

    Raises RetryError if exceeded attempts; callers should handle and log.
    """
    response = requests.get(url, params=params, headers=headers, timeout=settings.request_timeout_seconds)
    response.raise_for_status()
    return response.json()


def safe_parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Try ISO 8601 first
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        try:
            # Fallback to common RFC 2822-like format
            return datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")
        except Exception:
            return None


def make_stable_id(*parts: Iterable[str]) -> str:
    hasher = hashlib.sha256()
    for part in parts:
        hasher.update(str(part).encode("utf-8"))
        hasher.update(b"|")
    return hasher.hexdigest()[:16]


def text_contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def normalize_log_scale(value: Optional[float], default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return math.log10(max(value, 1.0))
    except Exception:
        return default


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)


