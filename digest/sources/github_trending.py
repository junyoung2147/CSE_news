import re

from bs4 import BeautifulSoup

from .. import config
from ..models import Item
from . import get

NAME = "github_trending"


def parse(html: str) -> list[Item]:
    items = []
    for row in BeautifulSoup(html, "html.parser").select("article.Box-row"):
        repo = row.h2.a["href"].strip("/")
        stars = row.select_one("span.d-inline-block.float-sm-right")  # "7,947 stars this week"
        lang = row.select_one('[itemprop="programmingLanguage"]')
        items.append(Item(
            source=NAME, category="dev", title=repo, url=f"https://github.com/{repo}",
            score=int(re.sub(r"\D", "", stars.get_text())) if stars else 0, score_type="stars_this_week",
            summary=row.p.get_text(" ", strip=True) if row.p else "",
            extra={"language": lang.get_text(strip=True)} if lang else {},
        ))
    return items


def fetch(start, end) -> list[Item]:
    # Trending is "this week" relative to now; it has no per-item dates, so the window is not applied.
    items = parse(get(config.URLS[NAME]).text)
    if not items:
        raise ValueError("no repositories parsed (page layout changed?)")
    return items
