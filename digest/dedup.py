import logging
import os

from .models import Item
from .normalize import make_id

log = logging.getLogger(__name__)


def merge(items: list[Item], priority: list[str]) -> list[Item]:
    """같은 id끼리 합친다. priority에서 앞선 소스(1차 출처)를 대표로 두고 나머지는 also_seen_in에 넣는다."""
    rank = {name: i for i, name in enumerate(priority)}
    groups: dict[str, Item] = {}
    for it in sorted(items, key=lambda i: (rank.get(i.source, len(rank)), -(i.score or 0))):
        rep = groups.setdefault(it.id, it)
        if rep is it:
            continue
        if it.source != rep.source and it.source not in rep.also_seen_in:
            rep.also_seen_in.append(it.source)
        rep.summary = rep.summary or it.summary
        rep.is_ai = rep.is_ai or it.is_ai
        for k, v in it.extra.items():
            rep.extra.setdefault(k, v)
    return list(groups.values())


def exclude(items: list[Item], path: str | None) -> list[Item]:
    """이미 다룬 URL 파일(한 줄에 하나)과 id가 같은 항목을 뺀다. 파일이 없으면 그대로 둔다."""
    if not path:
        return items
    if not os.path.exists(path):
        log.info("exclude file %s not found, skipping", path)
        return items
    with open(path, encoding="utf-8") as f:
        seen = {make_id(line) for line in f if line.strip()}
    kept = [i for i in items if i.id not in seen]
    log.info("excluded %d already-covered items", len(items) - len(kept))
    return kept
