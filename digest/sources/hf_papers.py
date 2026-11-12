from datetime import datetime, timedelta, timezone

from .. import config
from ..models import Item
from . import get

NAME = "hf_daily_papers"
KST = timezone(timedelta(hours=9))


def parse(data: list) -> list[Item]:
    """HF daily_papers 응답을 Item 목록으로 바꾼다 (url은 arXiv abs 링크)."""
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
    """기간에 걸친 KST 날짜마다 한 번씩 요청한다 (API가 일 단위라서)."""
    day, last = start.astimezone(KST).date(), end.astimezone(KST).date()
    items = []
    while day <= last:
        items += parse(get(config.URLS[NAME], date=day.isoformat()).json())
        day += timedelta(days=1)
    return items
