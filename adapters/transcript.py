from __future__ import annotations

import logging
from typing import Optional, Tuple

from youtube_transcript_api import YouTubeTranscriptApi
from datetime import timedelta

logger = logging.getLogger("MediaAggregatorMCP")


class TranscriptError(RuntimeError):
    """Custom exception for transcript-related errors."""
    pass

def _extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats."""
    try:
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "youtube.com/embed/" in url:
            return url.split("youtube.com/embed/")[1].split("?")[0]
        if "youtube.com/v/" in url:
            return url.split("youtube.com/v/")[1].split("?")[0]
        if "youtube.com/shorts/" in url:
            return url.split("youtube.com/shorts/")[1].split("?")[0]
        return None
    except Exception:
        return None

def _format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    return str(timedelta(seconds=int(seconds)))

def fetch_youtube_transcript(video_url: str, *, language="en", include_metadata=True):
    try:
        video_id = _extract_video_id(video_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])

        segments = []
        full_text = ""

        for seg in transcript:
            start = seg.get("start", 0.0)
            duration = seg.get("duration", 0.0)
            text = seg.get("text", "")

            segment_info = {
                "start": start,
                "end": start + duration,
                "text": text,
                "duration": duration,
            }

            if include_metadata:
                segment_info.update({
                    "start_formatted": _format_time(start),
                    "end_formatted": _format_time(start + duration),
                })

            segments.append(segment_info)
            full_text += text + " "

        return {
            "video_id": video_id,
            "language": language,
            "segments": segments,
            "text": full_text.strip(),
        }

    except Exception as e:
        return {"error": str(e)}


