from .. import config
from . import get, in_window, parse_feed

NAME = "geeknews"


def fetch(start, end):
    """GeekNews RSS에서 기간 내 글을 가져온다 (RSS에는 최신 20개만 있음)."""
    # shortcut: the RSS only holds the latest 20 topics (~half a day) and the HTML returns 403 to bots,
    # so a weekly run sees only the tail of the week. Upgrade if GeekNews offers a longer feed or API.
    return in_window(parse_feed(get(config.URLS[NAME]).content, NAME, "kr"), start, end)
