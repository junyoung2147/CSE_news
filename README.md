# CSE_news

매주 개발·AI 소식을 골라 해석과 함께 정리합니다. → **https://junyoung2147.github.io/CSE_news/**

## 동작 방식

| 일요일 (KST) | 담당 | 결과 |
|---|---|---|
| 20:00 | GitHub Actions가 수집 스크립트 실행 | `data/candidates/YYYY-MM-DD.json` |
| 22:00 | Claude Code 루틴이 [`prompts/weekly.md`](prompts/weekly.md)대로 선별·해석 | `docs/issues/YYYY-MM-DD.json` |
| 커밋 직후 | GitHub Pages의 정적 뷰어(`docs/`)가 JSON을 읽어 표시 | 사이트 갱신 |

이미 게시한 URL은 다음 수집에서 제외됩니다. 수집 스크립트는 LLM을 호출하지 않고 API 키도 쓰지 않습니다.

## 직접 실행

```bash
pip install -r requirements.txt
python -m digest.collect --exclude seen_urls.txt --out candidates.json   # 기본: 지난 7일
pytest                                                                   # fixture만 사용, 네트워크 없음
gh workflow run collect.yml                                              # Actions 수집을 수동 실행
```

옵션: `--start` / `--end YYYY-MM-DD`(KST, 종료일 포함), `--sources a,b`, `--verbose`. 모든 소스가 실패하면 종료 코드 1을 반환합니다. 소스별 개수, 키워드, URL은 [`digest/config.py`](digest/config.py)에 있습니다.

## 소스와 한계

| 소스 | 수집 방법 | 한계 |
|---|---|---|
| HF Daily Papers | 날짜별 API, upvotes 상위 15 | — |
| Hacker News | Algolia API, points 상위 20 | — |
| GitHub Trending | 주간 페이지 HTML, 상위 15 | 항목에 날짜가 없어 기간 지정이 적용되지 않음 |
| OpenAI · DeepMind | RSS | — |
| Anthropic | sitemap + 글 페이지 메타 태그 (RSS 없음) | 실행당 최대 30개 글 |
| Meta AI | 블로그 HTML의 날짜 (RSS 없음) | 최신 글이 오래돼 대부분 0개 |
| GeekNews | RSS | 최신 20개(약 반나절)만 있음, HTML은 봇에 403 |
| arXiv | API | 목록 수집이 아니라 초록이 없는 논문 보강용 |

HTML을 파싱하는 소스는 사이트 구조가 바뀌면 깨질 수 있습니다. 실패한 소스는 결과 파일의 `sources_status`에 기록됩니다.
