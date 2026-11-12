# 주간 소식 작성 지시서 (Claude 루틴용)

이 저장소에서 이번 주 "개발·AI 주간 소식" 한 호를 만들어 main에 push합니다. 아래 순서를 그대로 따르세요.

## 1. 입력 확인
1. `data/candidates/`에서 파일 이름(YYYY-MM-DD.json)이 가장 최근인 파일을 엽니다.
2. `generated_at`이 지금보다 **36시간 넘게 오래됐으면** 이번 주 수집이 실패한 것입니다. 아무것도 커밋하지 말고, 그 이유를 출력에 남기고 끝냅니다.
3. 호 날짜(`<date>`)는 그 candidates 파일 이름의 날짜를 씁니다. `docs/issues/<date>.json`이 이미 있으면 다시 쓰고, index에서는 교체합니다.

## 2. 선별
- 총 **15~20개**를 고릅니다. 카테고리 비중은 **AI 연구 40 / AI 업계 30 / 개발 20 / 국내 10**(%)을 목표로 합니다. 한 카테고리에 좋은 후보가 모자라면 다른 카테고리로 채워도 됩니다.
- 판단 근거는 candidates 파일 안의 정보뿐입니다. 웹 검색이나 링크 열기는 하지 않습니다.
- 참고 신호:
  - `also_seen_in`이 있는 항목은 여러 곳에서 주목받은 것이라 우선합니다.
  - `score`는 소스마다 단위가 다르므로(upvotes, points, stars_this_week) **같은 소스 안에서만** 비교합니다.
  - `dev`·`kr` 항목은 `is_ai`가 true인 것과 아닌 것을 섞어, 개발 소식이 AI로만 채워지지 않게 합니다.
  - 광고성 글, 채용 공고, 단순 사례 소개(고객사 인터뷰 등)는 뺍니다.
- `sources_status`에서 `ok: false`인 소스는 이번 호에서 빠진 것입니다. 그런 소스가 있으면 `intro` 끝에 짧게 밝힙니다(예: "이번 주 GeekNews 수집 실패").

## 3. 해석 작성
항목마다 `commentary`를 **한국어 2~3문장**으로 씁니다.
- 1문장: 무엇인지. 제목을 반복하지 말고 핵심 내용을 씁니다.
- 1~2문장: 왜 중요한지, 누구에게 의미가 있는지.
- 근거는 candidates의 `title`과 `summary`뿐입니다. summary에 없는 수치나 사실은 지어내지 않습니다. 정보가 부족하면 짧게 쓰는 게 낫습니다.
- 전문 용어는 영어를 함께 씁니다(예: "검색 증강 생성(RAG)").
- `title`은 원문 제목을 그대로 둡니다.

`intro`는 이번 주 흐름을 1~2문장으로 요약합니다.

## 4. 파일 쓰기
`docs/issues/<date>.json`:
```json
{
  "date": "2026-11-15",
  "title": "개발·AI 주간 소식 — 2026-11-15",
  "intro": "이번 주 흐름 요약",
  "items": [
    {
      "category": "ai_research",
      "title": "원문 제목",
      "url": "candidates의 url 그대로",
      "source": "candidates의 source 그대로",
      "also_seen_in": ["hacker_news"],
      "commentary": "해석 2~3문장"
    }
  ]
}
```
- `category`는 candidates 값 그대로 씁니다(`ai_research`, `ai_industry`, `dev`, `kr`).
- `url`은 **반드시 candidates의 `url`을 그대로** 씁니다. 다음 주 수집에서 이 URL로 이미 다룬 항목을 제외하기 때문입니다.
- items는 카테고리 순서(ai_research → ai_industry → dev → kr)로, 같은 카테고리 안에서는 중요한 순서로 둡니다.

`docs/issues/index.json`은 최신 호가 맨 앞에 오는 배열입니다. 같은 `date`가 있으면 교체합니다:
```json
[{ "date": "2026-11-15", "title": "개발·AI 주간 소식 — 2026-11-15", "count": 18 }]
```

파일은 손으로 JSON 문자열을 이어 붙이지 말고, Python `json.dump(..., ensure_ascii=False, indent=1)`로 씁니다.

## 5. 검증 후 커밋
1. 두 파일이 유효한 JSON인지 확인합니다. **실패하면 커밋하지 않습니다**(깨진 JSON은 사이트를 망가뜨립니다).
   ```bash
   python -m json.tool docs/issues/<date>.json > /dev/null && python -m json.tool docs/issues/index.json > /dev/null
   ```
2. 모든 `url`이 candidates 파일에 있는지 확인합니다.
3. 이 두 파일만 커밋해 main에 push합니다:
   ```
   docs: <date> 주간 소식 게시

   N개 항목 (AI 연구 a, AI 업계 b, 개발 c, 국내 d)
   ```
4. 출력에는 고른 항목 수, 카테고리별 개수, 실패한 소스를 남깁니다.

다른 파일(코드, `data/`, 페이지 파일)은 수정하지 않습니다.
