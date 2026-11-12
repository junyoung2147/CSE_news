from digest.collect import SOURCES, prepare, top_n
from digest.dedup import exclude, merge
from digest.models import Item


def _item(source, url, score=None, **kw):
    it = Item(source=source, category=kw.pop("category", "dev"), title="t", url=url, score=score, **kw)
    prepare(it)
    return it


def test_same_paper_from_hf_and_hn_merges():
    hf = _item("hf_daily_papers", "https://arxiv.org/abs/2611.01234", 99, category="ai_research", summary="abs")
    hn = _item("hacker_news", "http://arxiv.org/pdf/2611.01234v1", 340, extra={"hn_points": 340})
    out = merge([hn, hf], list(SOURCES))
    assert len(out) == 1
    assert out[0].source == "hf_daily_papers"
    assert out[0].also_seen_in == ["hacker_news"]
    assert out[0].extra["hn_points"] == 340


def test_hn_github_link_merges_with_trending():
    gh = _item("github_trending", "https://github.com/Owner/Repo", 500)
    hn = _item("hacker_news", "http://www.github.com/owner/repo/?utm_source=hn", 80)
    out = merge([hn, gh], list(SOURCES))
    assert [(i.source, i.also_seen_in) for i in out] == [("github_trending", ["hacker_news"])]


def test_exclude(tmp_path):
    a = _item("hacker_news", "https://example.com/post", 10)
    b = _item("hacker_news", "https://arxiv.org/abs/2611.00001", 10)
    c = _item("hacker_news", "https://keep.me/x", 10)
    seen = tmp_path / "seen.txt"
    seen.write_text("http://www.example.com/post/?utm_source=x\nhttps://huggingface.co/papers/2611.00001\n\n")
    assert exclude([a, b, c], str(seen)) == [c]
    assert exclude([a, b, c], str(tmp_path / "missing.txt")) == [a, b, c]


def test_top_n_is_per_source():
    hn = [_item("hacker_news", f"https://h.com/{i}", i) for i in range(30)]
    lab = [_item("openai_news", f"https://o.com/{i}", category="ai_industry") for i in range(5)]
    out = top_n(hn + lab)
    assert sum(i.source == "hacker_news" for i in out) == 20
    assert min(i.score for i in out if i.source == "hacker_news") == 10
    assert sum(i.source == "openai_news" for i in out) == 5
