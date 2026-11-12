"""Every tunable value lives here."""

USER_AGENT = "dev-ai-digest/0.1 (+https://github.com/junyoung2147/CSE_news)"
TIMEOUT = 15        # seconds per request
RETRIES = 2         # extra attempts after the first, exponential backoff
HOST_DELAY = 0.7    # seconds between requests to the same host

# Per-source cap after merge/exclude. Sources not listed keep everything in the window.
TOP_N = {
    "hf_daily_papers": 15,
    "hacker_news": 20,
    "github_trending": 15,
    "geeknews": 15,
}

SUMMARY_MAX = 300
MAX_OUTPUT_BYTES = 60_000
ANTHROPIC_MAX_ARTICLES = 30  # article pages fetched per run (sitemap lastmod newest first)

URLS = {
    "hf_daily_papers": "https://huggingface.co/api/daily_papers",
    "anthropic_sitemap": "https://www.anthropic.com/sitemap.xml",
    "openai_news": "https://openai.com/news/rss.xml",
    "deepmind_blog": "https://deepmind.google/blog/rss.xml",
    "meta_ai_blog": "https://ai.meta.com/blog/",
    "hacker_news": "https://hn.algolia.com/api/v1/search",
    "github_trending": "https://github.com/trending?since=weekly",
    "geeknews": "https://news.hada.io/rss/news",
    "arxiv": "https://export.arxiv.org/api/query",
}

HN_MIN_POINTS = 50

# Matched case-insensitively, not inside a longer ASCII word ("said" does not match "ai").
AI_KEYWORDS = [
    "AI", "LLM", "LLMs", "GPT", "Claude", "Gemini", "Llama", "OpenAI", "Anthropic", "DeepMind",
    "model", "models", "transformer", "transformers", "diffusion", "agent", "agents", "agentic",
    "neural", "machine learning", "deep learning", "RAG", "MCP", "fine-tuning", "inference",
    "인공지능", "머신러닝", "딥러닝", "에이전트", "모델", "언어모델",
]
