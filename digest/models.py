from dataclasses import asdict, dataclass, field
from datetime import datetime


@dataclass
class Item:
    source: str
    category: str
    title: str
    url: str
    published_at: datetime | None = None
    score: int | None = None
    score_type: str | None = None
    summary: str = ""
    is_ai: bool | None = None
    arxiv_id: str | None = None
    extra: dict = field(default_factory=dict)
    also_seen_in: list = field(default_factory=list)
    id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["published_at"] = self.published_at.isoformat() if self.published_at else None
        order = ["id", "source", "also_seen_in", "category", "is_ai", "title", "url",
                 "published_at", "score", "score_type", "summary", "arxiv_id", "extra"]
        return {k: d[k] for k in order}
