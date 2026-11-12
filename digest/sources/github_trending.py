import re

from bs4 import BeautifulSoup

from .. import config
from ..models import Item
from . import get

NAME = "github_trending"


def parse(html: str) -> list[Item]:
    """Trending HTML의 저장소 행을 Item 목록으로 바꾼다. score는 이번 주 스타 수."""
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
    """주간 Trending을 가져온다. 항목에 날짜가 없어 기간 필터는 적용하지 않는다."""
    # Trending is "this week" relative to now; it has no per-item dates, so the window is not applied.
    items = parse(get(config.URLS[NAME]).text)
    if not items:
        raise ValueError("no repositories parsed (page layout changed?)")
    return items
