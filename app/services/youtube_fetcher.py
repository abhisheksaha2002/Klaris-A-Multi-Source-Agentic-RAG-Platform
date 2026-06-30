import re
from typing import List, Dict
from youtube_transcript_api import YouTubeTranscriptApi


def fetch_youtube_transcript(url: str) -> List[Dict[str, str]]:
    video_id = _extract_video_id(url)
    transcript_segments = YouTubeTranscriptApi.get_transcript(video_id)
    texts = [segment["text"] for segment in transcript_segments]
    full_transcript = " ".join(texts)
    return [{"content": full_transcript, "path": f"youtube://{video_id}"}]


def _extract_video_id(url: str) -> str:
    patterns = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url}")
