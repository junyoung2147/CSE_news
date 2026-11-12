from datetime import datetime, timezone

from .. import config
from ..models import Item
from . import get

NAME = "hacker_news"


def parse(data: dict) -> list[Item]:
    items = []
    for h in data["hits"]:
        hn_url = f"https://news.ycombinator.com/item?id={h['objectID']}"
        items.append(Item(
            source=NAME, category="dev", title=h["title"], url=h.get("url") or hn_url,
            published_at=datetime.fromtimestamp(h["created_at_i"], timezone.utc),
            score=h["points"], score_type="points",
            extra={"hn_points": h["points"], "hn_comments": h.get("num_comments") or 0, "hn_url": hn_url},
        ))
    return items


def fetch(start: datetime, end: datetime) -> list[Item]:
    # /search ranks by popularity, so the first 1000 hits are the top stories of the window.
    data = get(
        config.URLS[NAME], tags="story", hitsPerPage=1000,
        numericFilters=f"created_at_i>{int(start.timestamp())},created_at_i<{int(end.timestamp())},"
                       f"points>{config.HN_MIN_POINTS}",
        attributesToRetrieve="title,url,points,num_comments,created_at_i,objectID",
    ).json()
    return parse(data)
