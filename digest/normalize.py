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
    p = urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    query = urlencode([(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _TRACKING.match(k)])
    return urlunsplit(("https", host, p.path.rstrip("/"), query, ""))


def arxiv_id(url: str) -> str | None:
    m = _ARXIV.search(url)
    return m.group(1) if m else None


def github_repo(url: str) -> str | None:
    p = urlsplit(normalize_url(url))
    parts = [s for s in p.path.split("/") if s]
    # Only repo root links: an issue/PR/file link is its own story and must not be excluded with the repo.
    if p.netloc != "github.com" or len(parts) != 2 or parts[0].lower() in _GH_RESERVED:
        return None
    return f"{parts[0]}/{parts[1].removesuffix('.git')}".lower()  # GitHub names are case-insensitive


def make_id(url: str) -> str:
    if a := arxiv_id(url):
        return f"arxiv:{a}"
    if g := github_repo(url):
        return f"gh:{g}"
    return "url:" + hashlib.sha1(normalize_url(url).encode()).hexdigest()[:16]


def clean_summary(text: str, limit: int = config.SUMMARY_MAX) -> str:
    text = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text or "")).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def is_ai(text: str) -> bool:
    return bool(_AI.search(text or ""))
