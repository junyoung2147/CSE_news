from datetime import datetime, timedelta, timezone

from .. import config
from ..models import Item
from . import get

NAME = "hf_daily_papers"
KST = timezone(timedelta(hours=9))


def parse(data: list) -> list[Item]:
    items = []
    for p in data:
        paper = p["paper"]
        items.append(Item(
            source=NAME, category="ai_research", title=paper["title"],
            url=f"https://arxiv.org/abs/{paper['id']}", arxiv_id=paper["id"],
            published_at=datetime.fromisoformat(p["publishedAt"]),
            score=paper.get("upvotes", 0), score_type="upvotes",
            summary=paper.get("summary", ""), is_ai=True,
        ))
    return items


def fetch(start: datetime, end: datetime) -> list[Item]:
    """One request per KST calendar day touched by the window (the API is day-granular)."""
    day, last = start.astimezone(KST).date(), end.astimezone(KST).date()
    items = []
    while day <= last:
        items += parse(get(config.URLS[NAME], date=day.isoformat()).json())
        day += timedelta(days=1)
    return items
