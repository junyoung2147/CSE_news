"""AI lab news: OpenAI/DeepMind via RSS; Anthropic and Meta have no RSS (checked 2026-11-12)."""
import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from .. import config
from ..models import Item
from . import get, in_window, parse_feed

log = logging.getLogger(__name__)
CATEGORY = "ai_industry"


def openai(start, end):
    """OpenAI News RSS에서 기간 내 글을 가져온다."""
    return in_window(parse_feed(get(config.URLS["openai_news"]).content, "openai_news", CATEGORY), start, end)


def deepmind(start, end):
    """Google DeepMind 블로그 RSS에서 기간 내 글을 가져온다."""
    return in_window(parse_feed(get(config.URLS["deepmind_blog"]).content, "deepmind_blog", CATEGORY), start, end)


# --- Anthropic: /news is a JS-rendered list without dates, so use sitemap lastmod + each article's meta tags.
_SITEMAP_ENTRY = re.compile(r"<loc>(https://www\.anthropic\.com/news/[^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>")


def parse_anthropic_sitemap(xml: str, since: datetime) -> list[str]:
    """sitemap에서 lastmod가 since 이후인 /news/ 주소를 최신순으로 뽑는다."""
    entries = [(u, datetime.fromisoformat(m)) for u, m in _SITEMAP_ENTRY.findall(xml)]
    return [u for u, m in sorted(entries, key=lambda e: e[1], reverse=True) if m >= since]


def parse_anthropic_article(html: str, url: str) -> Item | None:
    """글 페이지 meta 태그에서 제목·발행일·설명을 읽는다. 발행일이 없으면 None."""
    soup = BeautifulSoup(html, "html.parser")
    published = soup.find("meta", property="article:published_time")
    if not published:  # category/index pages under /news/ have no publish date
        return None
    title = soup.find("meta", property="og:title")
    desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", property="og:description")
    return Item(
        source="anthropic_news", category=CATEGORY, url=url,
        title=(title["content"] if title else soup.title.get_text()).removesuffix(" \\ Anthropic").strip(),
        published_at=datetime.fromisoformat(published["content"]),
        summary=desc["content"] if desc else "",
    )


def anthropic(start, end):
    """sitemap으로 후보 글을 고르고 각 글의 발행일로 기간을 다시 거른다."""
    urls = parse_anthropic_sitemap(get(config.URLS["anthropic_sitemap"]).text, start)
    items = []
    for url in urls[: config.ANTHROPIC_MAX_ARTICLES]:
        try:
            if item := parse_anthropic_article(get(url).text, url):
                items.append(item)
        except Exception as e:  # one broken article should not drop the whole source
            log.warning("anthropic article %s failed: %s", url, e)
    return in_window(items, start, end)


# --- Meta: no RSS and the gz sitemap comes back empty; the blog HTML has "Month D, YYYY" dates near each card.
_META_DATE = re.compile(r"^\s*[A-Z][a-z]+ \d{1,2}, 20\d\d\s*$")
_META_LINK = re.compile(r"^https://ai\.meta\.com/blog/[a-z0-9-]+/?$")


def _meta_date(text: str) -> datetime | None:
    """'July 9, 2026' / 'Jul 9, 2026' 형식 날짜를 UTC datetime으로 바꾼다."""
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def parse_meta(html: str) -> list[Item]:
    """Meta 블로그 HTML에서 날짜 문자열과 같은 카드 안의 글 링크를 짝지어 Item을 만든다."""
    soup = BeautifulSoup(html, "html.parser")
    items: dict[str, Item] = {}
    for date_text in soup.find_all(string=_META_DATE):
        node, link = date_text.parent, None
        for _ in range(8):  # climb to the card that holds this date and its link
            if node is None or (link := node.find("a", href=_META_LINK)):
                break
            node = node.parent
        published = _meta_date(date_text)
        if not link or not published or link["href"] in items:
            continue
        title = max((a.get_text(" ", strip=True) for a in node.find_all("a", href=link["href"])), key=len)
        items[link["href"]] = Item(source="meta_ai_blog", category=CATEGORY, title=title,
                                   url=link["href"], published_at=published)
    return list(items.values())


def meta(start, end):
    """Meta AI 블로그 첫 페이지에서 기간 내 글을 가져온다."""
    return in_window(parse_meta(get(config.URLS["meta_ai_blog"]).text), start, end)
