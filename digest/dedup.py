import logging
import os

from .models import Item
from .normalize import make_id

log = logging.getLogger(__name__)


def merge(items: list[Item], priority: list[str]) -> list[Item]:
    """Collapse items sharing an id. The source earliest in `priority` (the primary source) is kept."""
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
