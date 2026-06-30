from app.models.schemas import SourceType


def detect_url_type(url: str) -> SourceType:
    url_lower = url.lower()
    if "github.com" in url_lower:
        return SourceType.GITHUB
    if "youtube.com/watch" in url_lower or "youtu.be/" in url_lower:
        return SourceType.YOUTUBE
    return SourceType.WEB
