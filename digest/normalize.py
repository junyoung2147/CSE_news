import hashlib
import html
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import config

_TRACKING = re.compile(r"^(utm_.*|ref|ref_src|fbclid|gclid|mc_cid|mc_eid)$", re.I)
_ARXIV = re.compile(r"(?:arxiv\.org/(?:abs|pdf)|huggingface\.co/papers)/(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
_GH_RESERVED = {"trending", "topics", "orgs", "sponsors", "features", "marketplace", "settings",
                "about", "pricing", "collections", "explore", "login", "search", "apps", "enterprise"}
_AI = re.compile(
    r"(?<![A-Za-z0-9])(?:" + "|".join(re.escape(k) for k in config.AI_KEYWORDS) + r")(?![A-Za-z0-9])",
    re.I,
)


def normalize_url(url: str) -> str:
    """추적 파라미터·www·끝 슬래시·fragment를 없애고 https로 맞춘 URL을 돌려준다."""
    p = urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _TRACKING.match(k)])
    return urlunsplit(("https", host, p.path.rstrip("/"), query, ""))


def arxiv_id(url: str) -> str | None:
    """arXiv/HF Papers 링크에서 버전을 뺀 arXiv ID를 뽑는다. 없으면 None."""
    m = _ARXIV.search(url)
    return m.group(1) if m else None


def github_repo(url: str) -> str | None:
    """GitHub 저장소 루트 링크면 소문자 'owner/repo'를, 아니면 None을 돌려준다."""
    p = urlsplit(normalize_url(url))
    parts = [s for s in p.path.split("/") if s]
    # Only repo root links: an issue/PR/file link is its own story and must not be excluded with the repo.
    if p.netloc != "github.com" or len(parts) != 2 or parts[0].lower() in _GH_RESERVED:
        return None
    return f"{parts[0]}/{parts[1].removesuffix('.git')}".lower()  # GitHub names are case-insensitive


def make_id(url: str) -> str:
    """중복 판정 키를 만든다: arxiv:<id>, gh:<owner/repo>, 그 외에는 정규화 URL 해시."""
    if a := arxiv_id(url):
        return f"arxiv:{a}"
    if g := github_repo(url):
        return f"gh:{g}"
    return "url:" + hashlib.sha1(normalize_url(url).encode()).hexdigest()[:16]


def clean_summary(text: str, limit: int = config.SUMMARY_MAX) -> str:
    """HTML 태그·엔티티를 지우고 공백을 정리한 뒤 limit자로 자른다."""
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def is_ai(text: str) -> bool:
    """AI 관련 키워드가 들어 있는지 본다 (영문 단어 안의 부분 일치는 무시)."""
    return bool(_AI.search(text or ""))
