"""Shared HTTP + feed helpers for all sources."""
import logging
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit

import feedparser
import requests

from .. import config
from ..models import Item

log = logging.getLogger(__name__)
_session = requests.Session()
_session.headers["User-Agent"] = config.USER_AGENT
_last_hit: dict[str, float] = {}


def get(url: str, **params) -> requests.Response:
    """호스트별 간격을 두고 GET한다. 네트워크 오류·429·5xx는 재시도하고, 그 밖의 4xx는 바로 예외를 던진다."""
    host = urlsplit(url).netloc
    err: Exception | None = None
    for attempt in range(config.RETRIES + 1):
        wait = _last_hit.get(host, 0) + config.HOST_DELAY - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_hit[host] = time.monotonic()
        log.debug("GET %s %s", url, params or "")
        try:
            r = _session.get(url, params=params or None, timeout=config.TIMEOUT)
            if r.status_code < 500 and r.status_code != 429:
                r.raise_for_status()
                return r
            err = requests.HTTPError(f"HTTP {r.status_code}")
        except (requests.ConnectionError, requests.Timeout) as e:
            err = e
        if attempt < config.RETRIES:
            time.sleep(2 ** attempt)
    raise err


def parse_feed(content: bytes | str, source: str, category: str) -> list[Item]:
    """RSS/Atom 내용을 Item 목록으로 바꾼다. 날짜는 UTC로 둔다."""
    feed = feedparser.parse(content)
    if not feed.entries and feed.bozo:
        raise ValueError(f"unparseable feed: {feed.bozo_exception}")
    items = []
    for e in feed.entries:
        t = e.get("published_parsed") or e.get("updated_parsed")  # feedparser gives UTC struct_time
        items.append(Item(
            source=source, category=category, title=e.get("title", "").strip(), url=e.get("link", ""),
            published_at=datetime(*t[:6], tzinfo=timezone.utc) if t else None,
            summary=e.get("summary", ""),
        ))
    return items


def in_window(items: list[Item], start: datetime, end: datetime) -> list[Item]:
    """published_at이 [start, end) 안에 있는 항목만 남긴다."""
    return [i for i in items if i.published_at and start <= i.published_at < end]
