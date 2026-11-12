"""CLI: python -m digest.collect [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--exclude PATH] [--out PATH]"""
import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

from . import config
from .dedup import exclude, merge
from .models import Item
from .normalize import arxiv_id, clean_summary, is_ai, make_id, normalize_url
from .sources import arxiv, geeknews, github_trending, hacker_news, hf_papers, labs

log = logging.getLogger("digest")
KST = timezone(timedelta(hours=9))

# Order = merge priority: when the same item shows up twice, the earlier source is the representative.
SOURCES = {
    "hf_daily_papers": hf_papers.fetch,
    "anthropic_news": labs.anthropic,
    "openai_news": labs.openai,
    "deepmind_blog": labs.deepmind,
    "meta_ai_blog": labs.meta,
    "github_trending": github_trending.fetch,
    "hacker_news": hacker_news.fetch,
    "geeknews": geeknews.fetch,
}


def window(start: str | None, end: str | None, now: datetime) -> tuple[datetime, datetime]:
    """KST 날짜 옵션을 UTC 기간으로 바꾼다. --end는 그날 24:00까지 포함한다."""
    e = datetime.combine(date.fromisoformat(end) + timedelta(days=1), time(), KST) if end else now
    s = datetime.combine(date.fromisoformat(start), time(), KST) if start else e - timedelta(days=7)
    if s >= e:
        raise SystemExit("--start must be before --end")
    return s.astimezone(timezone.utc), e.astimezone(timezone.utc)


def prepare(it: Item) -> None:
    """URL 정규화, arXiv ID·id 계산, 요약 정리, is_ai 판정을 한다."""
    it.url = normalize_url(it.url)
    it.arxiv_id = it.arxiv_id or arxiv_id(it.url)
    it.id = make_id(it.url)
    it.summary = clean_summary(it.summary)
    if it.is_ai is None:
        it.is_ai = True if it.category.startswith("ai_") else is_ai(f"{it.title} {it.summary}")


def top_n(items: list[Item]) -> list[Item]:
    """소스별로 점수순 상위 N개만 남긴다 (점수가 없으면 원래 순서 유지)."""
    by_source = defaultdict(list)
    for it in items:
        by_source[it.source].append(it)
    out = []
    for source, group in by_source.items():
        group.sort(key=lambda i: -(i.score or 0))  # stable: unscored feeds keep their own order
        out += group[: config.TOP_N.get(source, len(group))]
    return out


def render(doc: dict, items: list[Item]) -> str:
    """JSON으로 직렬화한다. 크기 한도를 넘으면 summary를 단계적으로 줄인다."""
    for limit in (config.SUMMARY_MAX, 200, 120, 60, 0):
        for it in items:
            it.summary = clean_summary(it.summary, limit) if limit else ""
        text = json.dumps({**doc, "items": [i.to_dict() for i in items]}, ensure_ascii=False, indent=1)
        if len(text.encode()) <= config.MAX_OUTPUT_BYTES:
            break
        log.info("output %d bytes > %d, shortening summaries", len(text.encode()), config.MAX_OUTPUT_BYTES)
    else:
        log.warning("output still over %d bytes", config.MAX_OUTPUT_BYTES)
    return text


def main(argv: list[str] | None = None) -> int:
    """CLI 진입점. 수집→정규화→합치기→제외→상위 N→보강→출력 후 종료 코드를 돌려준다."""
    ap = argparse.ArgumentParser(prog="python -m digest.collect", description=__doc__)
    ap.add_argument("--start", help="start date YYYY-MM-DD (KST, default: 7 days before end)")
    ap.add_argument("--end", help="end date YYYY-MM-DD, inclusive (KST, default: now)")
    ap.add_argument("--exclude", help="file with already-covered URLs, one per line")
    ap.add_argument("--out", default="candidates.json")
    ap.add_argument("--sources", help="comma-separated subset: " + ",".join(SOURCES))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s %(name)s: %(message)s")

    names = args.sources.split(",") if args.sources else list(SOURCES)
    if unknown := set(names) - set(SOURCES):
        ap.error(f"unknown sources: {', '.join(sorted(unknown))}")

    now = datetime.now(KST).replace(microsecond=0)
    start, end = window(args.start, args.end, now)
    log.info("window %s .. %s", start.astimezone(KST).isoformat(), end.astimezone(KST).isoformat())

    items, status = [], []
    for name in names:
        try:
            got = SOURCES[name](start, end)
            status.append({"name": name, "ok": True, "fetched": len(got), "kept": 0, "error": None})
            items += got
            log.info("%s: %d items", name, len(got))
        except Exception as e:  # one source failing must not stop the run
            log.warning("%s failed: %s", name, e, exc_info=args.verbose)
            status.append({"name": name, "ok": False, "fetched": 0, "kept": 0, "error": f"{type(e).__name__}: {e}"[:200]})

    for it in items:
        prepare(it)
    items = merge(items, list(SOURCES))
    items = exclude(items, args.exclude)
    items = top_n(items)
    arxiv.enrich(items)
    for it in items:
        it.summary = clean_summary(it.summary)
    kept = defaultdict(int)
    for it in items:
        kept[it.source] += 1
    for s in status:
        s["kept"] = kept[s["name"]]

    doc = {
        "generated_at": now.isoformat(),
        "window": {"start": start.astimezone(KST).isoformat(), "end": end.astimezone(KST).isoformat()},
        "sources_status": status,
    }
    text = render(doc, items)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:  # keep size == measured bytes on Windows
        f.write(text)
    log.info("wrote %s: %d items, %d bytes", args.out, len(items), len(text.encode()))
    return 0 if any(s["ok"] for s in status) else 1


if __name__ == "__main__":
    sys.exit(main())
