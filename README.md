# CSE_news — 개발·AI 주간 소식 후보 수집기

매주 개발·AI 소식 정리 자동화의 **1단계(수집 + 1차 거르기)** 스크립트입니다. LLM을 호출하지 않고, 정해진 규칙대로 모으고 걸러서 JSON 파일 하나(`candidates.json`, 60KB 이하)를 만듭니다. 설계는 [PLAN.md](PLAN.md)를 보세요.

## 사용법

```bash
git clone https://github.com/junyoung2147/CSE_news
cd CSE_news
pip install -r requirements.txt
python -m digest.collect --exclude seen_urls.txt --out candidates.json
```

| 옵션 | 설명 |
|---|---|
| `--start YYYY-MM-DD` | 시작일 (KST 00:00, 기본: 종료 7일 전) |
| `--end YYYY-MM-DD` | 종료일, **그날 포함** (KST 24:00까지, 기본: 지금) |
| `--exclude PATH` | 이미 다룬 URL 목록(한 줄에 하나). 없는 파일이면 건너뜀 |
| `--out PATH` | 출력 파일 (기본 `candidates.json`) |
| `--sources a,b` | 일부 소스만 실행: `hf_daily_papers, anthropic_news, openai_news, deepmind_blog, meta_ai_blog, github_trending, hacker_news, geeknews` |
| `--verbose` | 요청 단위 DEBUG 로그 |

- 로그는 stderr로만 나가고 stdout은 비어 있습니다.
- 종료 코드: 소스가 하나라도 성공하면 0, **모두 실패하면 1** (이때도 파일은 `sources_status`와 함께 써집니다).
- 소스별 상위 N개, 키워드, 타임아웃, URL은 모두 `digest/config.py` 한 곳에 있습니다.
- 테스트: `pytest` (저장해 둔 실제 응답 `tests/fixtures/`만 사용, 네트워크 없음)

## 처리 순서

수집 → 정규화(URL·arXiv ID·`owner/repo`, 요약 300자) → 합치기 → 지난 호 제외 → 소스별 상위 N → arXiv 초록 보강 → 출력(60KB가 넘으면 summary를 200→120→60자로 줄임)

- **합치기:** 같은 `id`가 여러 소스에 있으면 1차 출처를 대표로 둡니다. 우선순위는 HF → Anthropic → OpenAI → DeepMind → Meta → GitHub Trending → HN → GeekNews 순이고, 나머지 소스는 `also_seen_in`에 넣고 `extra`(예: `hn_points`)도 합칩니다.
- **`id`:** `arxiv:<id>`, `gh:<owner>/<repo>`(저장소 루트 링크만, 이슈·PR 링크는 별도 항목), 그 외에는 정규화한 URL의 SHA-1 16자리입니다.
- **`--exclude`:** 각 줄을 같은 방식으로 `id`로 바꿔 비교합니다. 그래서 `http://www.`, `utm_*`, `/pdf/` 같은 형태 차이가 있어도 걸러집니다.
- **`is_ai`:** `ai_*` 카테고리는 항상 true입니다. HN·GitHub·GeekNews는 `config.AI_KEYWORDS` 키워드로 판정합니다. 영문 단어 안의 부분 일치는 무시해서 "said"는 "ai"로 잡히지 않고, 한글 조사가 붙은 "AI와"는 잡힙니다.

## 소스별 확인 결과 (2026-11-12 실측)

| 소스 | 실제 방법 | 결과 |
|---|---|---|
| HF Daily Papers | `huggingface.co/api/daily_papers?date=YYYY-MM-DD`, KST 날짜별로 호출 | ✅ JSON에 `paper.id`(arXiv), `upvotes`, `summary`(초록)가 있어 arXiv 보강이 필요 없음 |
| arXiv | `export.arxiv.org/api/query?id_list=…` (https) | ✅ 초록이 없는 arXiv 항목(주로 HN 출처)만 한 번에 묶어서 보강 |
| Anthropic News | `/rss.xml`은 404이고, `/news` 목록 HTML에는 날짜가 없음 → `sitemap.xml`에서 `/news/` 중 lastmod가 기간 내인 글을 고르고, 각 글의 `article:published_time`으로 다시 거름 | ✅ 실행당 최대 30개 글 요청 |
| OpenAI News | RSS `openai.com/news/rss.xml` | ✅ (전체 아카이브 약 1,400개, 840KB) |
| Google DeepMind | RSS `deepmind.google/blog/rss.xml` | ✅ 최근 100개 |
| Meta AI Blog | `/blog/rss/`는 404이고, robots.txt의 sitemap(.gz)은 빈 응답 → `ai.meta.com/blog/` HTML에서 "Month D, YYYY" 날짜와 카드 링크를 짝지음 | ✅ 파싱은 되지만 목록 첫 페이지의 최신 글이 2026-07이라, 지금은 주간 결과가 보통 0개 |
| Hacker News | Algolia `/api/v1/search?tags=story&numericFilters=created_at_i>…,created_at_i<…,points>50&hitsPerPage=1000` | ✅ 인기순 정렬이라 상위 1000개 안에 주간 상위가 다 들어옴 |
| GitHub Trending | `github.com/trending?since=weekly`의 `article.Box-row` | ✅ 약 13~25개, "N stars this week"를 score로 사용 |
| GeekNews | RSS `news.hada.io/rss/news` → feedburner로 리다이렉트 | ⚠️ 최신 20개만 들어 있음(약 반나절 분량). HTML은 봇에 403을 반환함 |

## 알려진 한계

- **GeekNews는 주간 전체를 못 가져옵니다.** RSS에 최신 20개만 있고, HTML(`/`, `/weekly`)은 403입니다. 차단을 우회하지 않으므로 실행 시점 직전 반나절 분량만 수집됩니다. 점수 정보가 없어 피드 순서(최신순)로 상위 15개를 남깁니다.
- **GitHub Trending에는 날짜가 없습니다.** 실행 시점 기준 "이번 주"라서 `--start/--end`가 적용되지 않고 `published_at`은 null입니다.
- **Anthropic, Meta, GitHub는 HTML·sitemap 구조에 의존합니다.** 사이트가 바뀌면 깨지는데, 깨지면 해당 소스가 `ok: false` 또는 0개로 나옵니다. Meta 날짜는 일 단위(UTC 00:00으로 취급)입니다.
- **Anthropic 기간 판정은 sitemap lastmod로 먼저 거릅니다.** 기간 안에 발행됐는데 lastmod가 없거나 더 이른 글은 빠질 수 있습니다(실제로는 lastmod ≥ 발행일).
- `is_ai`는 단순 키워드 매칭이라 "model", "agent" 같은 일반 단어 때문에 오탐이 있을 수 있습니다. 참고용입니다.
- 전체 실행은 약 20초입니다(목표 2분). 요청은 순차로 보내고, 같은 호스트에는 0.7초 간격을 둡니다. 타임아웃은 15초, 네트워크 오류·429·5xx는 최대 2번 재시도합니다.
