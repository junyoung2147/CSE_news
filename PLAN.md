# CSE_news 수집 스크립트 계획

## 0. 이 문서의 목적

매주 개발·AI 소식을 해석과 함께 정리하는 자동화의 **1단계: 후보 수집 스크립트**를 만들기 위한 계획서입니다.
Claude Code에서 이 문서를 읽고 저장소와 스크립트를 구현합니다.

### 전체 시스템에서 이 저장소가 맡는 부분

> **2026-11-12 변경:** Cowork 예약 작업 + 아카이브 DB 구조를 버리고, 저장소 하나로 끝나는 구조로 바꿨습니다.
> GitHub Actions(수집) → Claude Code 클라우드 루틴(선별·해석) → GitHub Pages(정적 HTML+JS 뷰어).

| 단계 | 담당 | 결과물 |
|---|---|---|
| ① 수집 + ② 1차 거르기 | **이 스크립트**, GitHub Actions가 매주 일요일 20:00 KST에 실행 (`.github/workflows/collect.yml`) | `data/candidates/YYYY-MM-DD.json` 커밋 |
| ③ 선별 · ④ 해석 작성 | Claude Code 루틴, 일요일 22:00 KST (`prompts/weekly.md`를 따름) | `docs/issues/<date>.json` + `docs/issues/index.json` 커밋 |
| ⑤ 게시 | GitHub Pages가 `docs/`를 그대로 서빙. `app.js`가 JSON을 fetch해서 그림 | https://junyoung2147.github.io/CSE_news/ |

- 스크립트는 **LLM을 호출하지 않습니다.** 정해진 규칙에 따라 모으고 거르기만 합니다.
- "이미 다룬 링크"는 DB 대신 **게시된 호 JSON의 `url`**에서 뽑습니다(workflow에서 `jq`).

### Actions가 이 스크립트를 쓰는 방식 (인터페이스 계약)

```
1. pip install -r requirements.txt
2. jq -r '.items[].url' docs/issues/2*.json > seen_urls.txt
3. python -m digest.collect --exclude seen_urls.txt --out data/candidates/YYYY-MM-DD.json
4. 커밋 → Claude 루틴이 최신 candidates 파일만 읽고 선별
```

따라서 **명령 한 줄로 실행되고, 결과가 JSON 파일 하나로 나와야 합니다.**

---

## 1. 수집 기간

- 기본값: 실행 시점 기준 **지난 7일**. 실행은 매주 일요일 저녁(KST)입니다.
- `--start`, `--end` 옵션으로 기간을 직접 지정할 수 있습니다. 날짜는 `YYYY-MM-DD`, KST 기준입니다.
- 내부 시간은 모두 UTC로 다루고, 출력에는 ISO 8601 형식(타임존 포함)으로 씁니다.

## 2. 소스 (1군만)

| # | 소스 | 카테고리 | 수집 방법 | 1차 거르기 |
|---|---|---|---|---|
| 1 | Hugging Face Daily Papers | `ai_research` | 공개 API, 날짜별 조회 (`https://huggingface.co/api/daily_papers?date=YYYY-MM-DD`) × 7일 | 추천 수(upvotes) 상위 **15개** |
| 2 | arXiv | (보조) | 공개 API (`http://export.arxiv.org/api/query?id_list=...`) | **목록 수집에는 쓰지 않음.** 다른 소스에서 나온 arXiv ID의 초록·저자 보강용 |
| 3 | Anthropic News | `ai_industry` | 뉴스 페이지 HTML 파싱 (RSS가 있으면 RSS 우선) | 기간 내 전부 |
| 4 | OpenAI News | `ai_industry` | RSS (`https://openai.com/news/rss.xml`) | 기간 내 전부 |
| 5 | Google DeepMind Blog | `ai_industry` | RSS (`https://deepmind.google/blog/rss.xml`) | 기간 내 전부 |
| 6 | Meta AI Blog | `ai_industry` | 블로그 페이지 HTML 파싱 (RSS가 있으면 RSS 우선) | 기간 내 전부 |
| 7 | Hacker News | `dev` | Algolia 검색 API (`https://hn.algolia.com/api/v1/search?tags=story&numericFilters=created_at_i>START,created_at_i<END,points>50`) | 점수 상위 **20개** |
| 8 | GitHub Trending | `dev` | `https://github.com/trending?since=weekly` HTML 파싱 | 상위 **15개** (이번 주 스타 수 기준) |
| 9 | GeekNews | `kr` | RSS (`https://news.hada.io/rss/news`) | 기간 내 상위 **15개** |

> ⚠️ **위 URL과 API 형식은 모두 구현 전에 실제로 확인해야 합니다.** RSS가 없거나 주소가 바뀌었으면 대안(HTML 파싱, 다른 엔드포인트)을 찾고 README에 기록합니다.
> 페이지가 JavaScript로 렌더링되어 HTML 파싱이 안 되면, 브라우저 자동화는 쓰지 말고 sitemap.xml이나 내부 JSON 엔드포인트를 찾아봅니다. 그래도 안 되면 해당 소스를 "수집 실패"로 처리합니다.

- 소스별 상위 개수는 `config.py`나 `sources.yaml` 한 곳에서 바꿀 수 있게 합니다.
- **전체 점수순으로 자르지 않습니다.** 소스마다 점수 체계가 달라서, 소스별로 따로 상위 N개를 남깁니다.
- HN, GitHub, GeekNews 항목에는 간단한 키워드 기반 `is_ai` 플래그를 붙입니다. (예: LLM, GPT, Claude, model, transformer, diffusion, agent, AI, 인공지능 …) Claude가 카테고리 비중을 맞출 때 참고합니다.

## 3. 출력 형식 (`candidates.json`)

```json
{
  "generated_at": "2026-11-15T20:40:00+09:00",
  "window": { "start": "2026-11-08T20:40:00+09:00", "end": "2026-11-15T20:40:00+09:00" },
  "sources_status": [
    { "name": "hf_daily_papers", "ok": true,  "fetched": 132, "kept": 15, "error": null },
    { "name": "geeknews",        "ok": false, "fetched": 0,   "kept": 0,  "error": "HTTP 503" }
  ],
  "items": [
    {
      "id": "arxiv:2611.01234",
      "source": "hf_daily_papers",
      "also_seen_in": ["hacker_news"],
      "category": "ai_research",
      "is_ai": true,
      "title": "...",
      "url": "https://arxiv.org/abs/2611.01234",
      "published_at": "2026-11-10T09:00:00+00:00",
      "score": 214,
      "score_type": "upvotes",
      "summary": "300자 이내 요약 (RSS 설명, 초록 앞부분, 저장소 설명 등)",
      "arxiv_id": "2611.01234",
      "extra": { "hn_points": 340, "hn_comments": 120 }
    }
  ]
}
```

필드 규칙:

- `id`: 중복 판정 키. arXiv 논문이면 `arxiv:<id>`, GitHub 저장소면 `gh:<owner>/<repo>`, 그 외에는 정규화한 URL의 해시.
- `summary`: **최대 300자**. HTML 태그를 제거하고 공백을 정리합니다.
- `also_seen_in`: 같은 항목이 다른 소스에도 나왔을 때 그 소스 이름 목록. 중요도 신호로 씁니다.
- `extra`: 소스별 부가 정보. 자유 형식이지만 작게 유지합니다.
- **전체 파일 크기 목표: 60KB 이하.** Claude가 읽는 토큰을 줄이기 위해서입니다. 넘으면 summary를 더 줄입니다.

## 4. 중복 처리

1. **URL 정규화:** `utm_*`, `ref`, `fbclid` 같은 추적 파라미터와 끝의 `/`, `#fragment`를 제거합니다. `http`는 `https`로 바꾸고, `www.`를 제거하고, 호스트는 소문자로 바꿉니다.
2. **arXiv ID 추출:** `arxiv.org/abs/…`, `arxiv.org/pdf/…`, `huggingface.co/papers/…` 링크에서 ID를 뽑아 같은 논문을 하나로 합칩니다.
3. **GitHub 저장소:** HN에 올라온 GitHub 링크와 Trending 항목을 `owner/repo` 기준으로 합칩니다.
4. **합칠 때:** 점수가 높은 쪽(또는 1차 출처)을 대표로 두고, 다른 소스는 `also_seen_in`에 넣습니다.
5. **지난 호 제외:** `--exclude <파일>`로 받은 URL 목록(한 줄에 하나)을 같은 방식으로 정규화해서, 일치하는 항목을 뺍니다. 파일이 없으면 이 단계는 건너뜁니다.

순서: 수집 → 정규화 → 합치기 → 지난 호 제외 → 소스별 상위 N개 → 출력.

## 5. 오류 처리와 예의

- **소스 하나가 실패해도 전체는 계속 진행합니다.** 실패 내용은 `sources_status`에 기록합니다.
- 모든 소스가 실패했을 때만 종료 코드 1을 반환합니다.
- 요청 타임아웃 15초, 재시도 최대 2번(지수 백오프).
- 같은 호스트에는 요청 사이에 0.5~1초 간격을 둡니다.
- User-Agent에 프로젝트 이름과 저장소 URL을 넣습니다. (예: `dev-ai-digest/0.1 (+https://github.com/<user>/dev-ai-digest)`)
- 전체 실행 시간 목표: **2분 이내.**
- 로그는 stderr로 보내고, stdout은 깨끗하게 둡니다.

## 6. 기술 스택과 저장소 구조

- Python 3.11 이상
- 의존성은 최소한으로: `requests`, `feedparser`, `beautifulsoup4` (+ 테스트용 `pytest`)
- API 키나 비밀 정보는 **사용하지 않습니다.** 저장소가 공개라서 키가 필요한 소스는 넣지 않습니다.

```
dev-ai-digest/
├── README.md              # 사용법, 소스별 확인 결과, 알려진 한계
├── PLAN.md                # 이 문서
├── requirements.txt
├── digest/
│   ├── __init__.py
│   ├── collect.py         # CLI 진입점 (python -m digest.collect)
│   ├── config.py          # 소스별 상위 N, 키워드, 타임아웃 등
│   ├── models.py          # Item 데이터 구조
│   ├── normalize.py       # URL 정규화, arXiv ID 추출, 요약 자르기
│   ├── dedup.py           # 합치기, 지난 호 제외
│   └── sources/
│       ├── hf_papers.py
│       ├── arxiv.py
│       ├── labs.py        # Anthropic, OpenAI, DeepMind, Meta
│       ├── hacker_news.py
│       ├── github_trending.py
│       └── geeknews.py
└── tests/
    ├── fixtures/          # 저장해 둔 실제 응답 샘플 (HTML, RSS, JSON)
    ├── test_normalize.py
    ├── test_dedup.py
    └── test_sources.py    # fixture로 파서만 테스트 (네트워크 없이)
```

## 7. CLI

```
python -m digest.collect [옵션]

  --start YYYY-MM-DD     시작일 (KST, 기본: 7일 전)
  --end YYYY-MM-DD       종료일 (KST, 기본: 지금)
  --exclude PATH         이미 다룬 URL 목록 파일
  --out PATH             출력 파일 (기본: candidates.json)
  --sources a,b,c        일부 소스만 실행 (디버깅용)
  --verbose              자세한 로그
```

## 8. 완료 기준

- [ ] 각 소스의 실제 URL과 형식을 확인하고, 결과를 README에 기록함
- [ ] `python -m digest.collect` 한 줄로 실행되고 `candidates.json`이 생성됨
- [ ] 소스 하나를 일부러 실패시켜도(잘못된 URL 등) 나머지는 정상 출력되고, `sources_status`에 실패가 기록됨
- [ ] 같은 논문이 HF와 HN에 있을 때 하나로 합쳐지고 `also_seen_in`이 채워짐
- [ ] `--exclude` 파일에 있는 URL이 결과에서 빠짐
- [ ] 출력 파일이 60KB 이하
- [ ] fixture 기반 테스트가 네트워크 없이 통과함 (`pytest`)
- [ ] README에 사용법과 알려진 한계가 정리됨
- [ ] 공개 GitHub 저장소에 푸시됨

## 9. 이후 단계

1. ~~GitHub Actions runner에서 수동 실행해 사이트 접속 확인~~ (`gh workflow run collect.yml`)
2. ~~뷰어 페이지와 호 JSON 형식 만들기~~ (`docs/`, 형식은 `prompts/weekly.md`)
3. ~~루틴 작업 지시서 작성~~ (`prompts/weekly.md`: 선별 기준, 비중 AI 연구 40 / AI 업계 30 / 개발 20 / 국내 10)
4. Claude Code 루틴 등록 후 수동 실행으로 결과 검토하고 조정

## 10. 하지 않는 것

- LLM API 호출, 요약 생성
- 로그인이 필요한 사이트, 유료 매체, X(트위터), Reddit
- 브라우저 자동화(Playwright, Selenium)
- 데이터베이스, 서버, 빌드 단계가 있는 웹페이지 (뷰어는 JSON을 읽기만 하는 정적 HTML+JS 한 장)
