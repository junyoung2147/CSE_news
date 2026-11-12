"""Not a list source: fills abstracts/authors for arXiv items that arrived without one (e.g. from HN)."""
import logging

import feedparser

from .. import config
from ..models import Item
from ..normalize import arxiv_id
from . import get

log = logging.getLogger(__name__)


def parse(content: bytes | str) -> dict[str, dict]:
    """arXiv API 응답에서 ID별 초록과 저자를 뽑는다."""
    out = {}
    for e in feedparser.parse(content).entries:
        if aid := arxiv_id(e.get("id", "")):
            out[aid] = {"summary": e.get("summary", ""), "authors": [a.get("name") for a in e.get("authors", [])]}
    return out


def enrich(items: list[Item]) -> None:
    """초록이 없는 arXiv 항목만 한 번에 조회해 summary와 저자를 채운다. 실패해도 넘어간다."""
    need = [i for i in items if i.arxiv_id and not i.summary]
    if not need:
        return
    try:
        found = parse(get(config.URLS["arxiv"], id_list=",".join(i.arxiv_id for i in need),
                          max_results=len(need)).content)
    except Exception as e:  # enrichment is optional
        log.warning("arXiv enrichment failed: %s", e)
        return
    for i in need:
        if meta := found.get(i.arxiv_id):
            i.summary = meta["summary"]
            i.extra["authors"] = meta["authors"][:3]
