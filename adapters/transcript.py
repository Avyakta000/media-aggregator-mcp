from __future__ import annotations

import logging
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
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


def fetch_youtube_transcript(
    video_url: str,
    transcript_type: str = "auto",
    language: str = "en",
    include_metadata: bool = True,
):
    try:
        video_id = _extract_video_id(video_url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
        if transcript_type == "auto":
            transcript = YouTubeTranscriptApi().fetch(video_id, languages=[language])
            transcript_list = None  # fetch() doesn't return transcript object with metadata
            print("transcript_data auto:", transcript)
        elif transcript_type == "manual":
            transcript_list = YouTubeTranscriptApi().list(video_id)
            transcript = transcript_list.find_manually_created_transcript([language])
            print("transcript_data manual:", transcript)
        elif transcript_type == "generated":
            transcript_list = YouTubeTranscriptApi().list(video_id)
            transcript = transcript_list.find_generated_transcript([language])
            print("transcript_data generated:", transcript)
        else:
            raise ValueError(f"Invalid transcript type: {transcript_type}. Must be one of: auto, manual, generated")
        
        segments = []
        full_text = ""

        for seg in transcript:
            # handle both dictionary format (old API) and FetchedTranscriptSnippet objects (new API)
            if hasattr(seg, 'start'):
                start = seg.start
                duration = seg.duration
                text = seg.text
            else:
                # Dictionary format
                start = seg.get("start", 0.0)
                duration = seg.get("duration", 0.0)
                text = seg.get("text", "")

            segment_info = {
                "start": start,
                "end": start + duration,
                "text": text,
                "duration": duration,
            }

            # No additional metadata for segments

            segments.append(segment_info)
            full_text += text + " "

        result = {
            "video_id": video_id,
            "language": language,
            "segments": segments,
            "text": full_text.strip(),
        }
        
        if transcript_list and include_metadata:
            result.update({
                "transcript_language":transcript_list.language,
                "transcript_language_code": transcript_list.language_code,
                "is_generated": transcript_list.is_generated,
                "is_translatable": transcript_list.is_translatable,
                "translation_languages": transcript_list.translation_languages,
            })
        
        return result

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.error(f"No transcript available for {video_url}: {e}")
        return {"error": f"Transcript not available, {e}", "video_id": video_url}
    except Exception as e:
        logger.error(f"Error fetching transcript for video {video_url}: {e}")
        return {"error": str(e), "video_id": video_url}
