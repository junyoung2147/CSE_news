"""Parsers against saved real responses (fetched 2026-11-12). No network."""
import json
from datetime import datetime, timezone
from pathlib import Path

from digest.sources import arxiv, github_trending, hacker_news, hf_papers, labs, parse_feed

FX = Path(__file__).parent / "fixtures"


def _read(name):
    return (FX / name).read_text(encoding="utf-8")


def _ok(items, n):
    assert len(items) == n
    for i in items:
        assert i.title and i.url.startswith("http")


def test_hf_papers():
    items = hf_papers.parse(json.loads(_read("hf_daily_papers.json")))
    _ok(items, 3)
    assert items[0].arxiv_id and isinstance(items[0].score, int) and items[0].summary


def test_hacker_news():
    items = hacker_news.parse(json.loads(_read("hn.json")))
    _ok(items, 5)
    assert items[0].extra["hn_points"] == items[0].score


def test_github_trending():
    items = github_trending.parse(_read("github_trending.html"))
    _ok(items, 3)
    assert items[0].url == "https://github.com/NVIDIA/auto-ontology" and items[0].score > 0


def test_rss_feeds():
    for name, src in [("openai.xml", "openai_news"), ("deepmind.xml", "deepmind_blog"), ("geeknews.xml", "geeknews")]:
        items = parse_feed((FX / name).read_bytes(), src, "x")
        _ok(items, 3)
        assert all(i.published_at for i in items)


def test_anthropic():
    urls = labs.parse_anthropic_sitemap(_read("anthropic_sitemap.xml"), datetime(2026, 10, 1, tzinfo=timezone.utc))
    assert urls == ["https://www.anthropic.com/news/widening-conversation-ai",
                    "https://www.anthropic.com/news/wellbeing-research-grants"]  # newest lastmod first
    item = labs.parse_anthropic_article(_read("anthropic_article.html"), "https://www.anthropic.com/news/s1-sec")
    assert item.title.startswith("Anthropic files S-1")
    assert item.published_at == datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_meta():
    items = labs.parse_meta(_read("meta_blog.html"))
    assert len(items) >= 5
    assert all(i.published_at and i.url.startswith("https://ai.meta.com/blog/") for i in items)


def test_arxiv():
    found = arxiv.parse((FX / "arxiv.xml").read_bytes())
    assert len(found) == 2 and all(v["summary"] for v in found.values())
