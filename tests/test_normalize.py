from digest.normalize import arxiv_id, clean_summary, github_repo, is_ai, make_id, normalize_url


def test_normalize_url():
    assert normalize_url("http://WWW.Example.com/a/b/?utm_source=x&id=3&ref=hn&fbclid=z#top") == \
        "https://example.com/a/b?id=3"
    assert normalize_url("https://example.com/") == "https://example.com"


def test_arxiv_id_forms():
    for url in ("https://arxiv.org/abs/2611.01234v2", "http://arxiv.org/pdf/2611.01234.pdf",
                "https://huggingface.co/papers/2611.01234"):
        assert arxiv_id(url) == "2611.01234"
    assert arxiv_id("https://example.com/2611.01234") is None


def test_github_repo():
    assert github_repo("https://github.com/NVIDIA/Auto-Ontology/?utm_source=hn") == "nvidia/auto-ontology"
    assert github_repo("https://github.com/anthropics/claude-code/issues/1") is None
    assert github_repo("https://github.com/trending") is None
    assert make_id("https://www.github.com/a/b/") == "gh:a/b"


def test_make_id_same_url_variants():
    assert make_id("http://www.x.com/p?utm_medium=rss") == make_id("https://x.com/p/")


def test_clean_summary():
    assert clean_summary("<p>Hello&nbsp;  <b>world</b></p>\n") == "Hello world"
    s = clean_summary("a" * 500)
    assert len(s) == 300 and s.endswith("…")


def test_is_ai():
    assert is_ai("New LLM benchmark")
    assert is_ai("AI와 일할 때")
    assert is_ai("인공지능 규제")
    assert not is_ai("He said the rain stopped")
