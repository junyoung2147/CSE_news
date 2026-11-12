// 주간 소식 뷰어: issues/index.json으로 호 목록을 만들고, #YYYY-MM-DD 해시의 호를 그린다.
"use strict";

const CATEGORIES = [
  ["ai_research", "AI 연구"],
  ["ai_industry", "AI 업계"],
  ["dev", "개발"],
  ["kr", "국내"],
];
const SOURCE_TAGS = {
  hf_daily_papers: "hf",
  anthropic_news: "anthropic",
  openai_news: "openai",
  deepmind_blog: "deepmind",
  meta_ai_blog: "meta",
  hacker_news: "hn",
  github_trending: "gh",
  geeknews: "geeknews",
};
const IMPORTANCE = { 3: "핵심", 2: "주목", 1: "참고" };
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const main = document.getElementById("main");
const select = document.getElementById("issue-select");
let issues = [];

/** 캐시 없이 JSON을 가져온다. 실패하면 경로가 담긴 오류를 던진다. */
async function getJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`);
  try {
    return await res.json();
  } catch {
    throw new Error(`${path}: JSON 형식 오류`);
  }
}

/** 태그를 만들고 텍스트를 textContent로만 넣는다 (XSS 방지). */
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

/** http(s) 주소만 링크로 허용한다. */
function safeUrl(url) {
  try {
    const u = new URL(url);
    return u.protocol === "https:" || u.protocol === "http:" ? u.href : null;
  } catch {
    return null;
  }
}

/** 상태 메시지 하나만 보여준다. */
function showStatus(text, isError = false) {
  main.replaceChildren(el("p", isError ? "status error" : "status", text));
}

/** 중요도(1~3)를 돌려준다. 없거나 잘못된 값이면 0 (표시 안 함). */
function importanceOf(item) {
  return IMPORTANCE[item.importance] ? Number(item.importance) : 0;
}

/** 중요도를 칸 3개짜리 신호 막대로 만든다. 화면 낭독기에는 단계 이름을 읽어 준다. */
function renderSignal(level) {
  const signal = el("span", "signal");
  if (!level) return signal;
  signal.setAttribute("role", "img");
  signal.setAttribute("aria-label", `중요도 ${IMPORTANCE[level]}`);
  signal.title = IMPORTANCE[level];
  for (let i = 1; i <= 3; i++) signal.append(el("span", i <= level ? "cell on" : "cell"));
  return signal;
}

/** 항목 하나를 신호 막대 + 본문 두 칸으로 만든다. */
function renderItem(item) {
  const level = importanceOf(item);
  const row = el("article", level === 3 ? "item key" : "item");
  const body = el("div", "body");

  const h3 = el("h3");
  const href = safeUrl(item.url);
  if (href) {
    const a = el("a", null, item.title);
    a.href = href;
    a.rel = "noopener";
    h3.append(a);
  } else {
    h3.textContent = item.title;
  }
  body.append(h3);
  if (item.commentary) body.append(el("p", "commentary", item.commentary));

  const meta = el("p", "meta");
  const tags = [item.source, ...(item.also_seen_in || [])].filter(Boolean).map((s) => SOURCE_TAGS[s] || s);
  meta.append(el("span", "tags", tags.join(" · ")));
  if (href) meta.append(el("span", "host", new URL(href).hostname.replace(/^www\./, "")));
  body.append(meta);

  row.append(renderSignal(level), body);
  return row;
}

/** 카테고리 머리글: "## ai_research  AI 연구 ······ 7" */
function renderCategoryTitle(key, label, count) {
  const h = el("h2", "category-title");
  h.append(
    el("span", "hash", "##"),
    el("span", "key", key),
    el("span", "label", label),
    el("span", "leader"),
    el("span", "count", String(count))
  );
  return h;
}

/** 호 하나를 카테고리 섹션으로 나눠 그린다. */
function renderIssue(issue) {
  const items = issue.items || [];
  const frag = document.createDocumentFragment();

  const head = el("div", "issue-head");
  const title = el("h2", "issue-date", issue.date);
  title.append(el("span", "issue-count", `${items.length} items`));
  head.append(title);
  if (issue.intro) head.append(el("p", "intro", issue.intro));
  frag.append(head);

  const known = new Set(CATEGORIES.map(([key]) => key));
  for (const [key, label] of [...CATEGORIES, ["other", "기타"]]) {
    const list = items
      .filter((i) => (key === "other" ? !known.has(i.category) : i.category === key))
      .sort((a, b) => importanceOf(b) - importanceOf(a)); // 안정 정렬: 같은 단계는 원래 순서 유지
    if (!list.length) continue;
    const section = el("section", "category");
    section.append(renderCategoryTitle(key, label, list.length), ...list.map(renderItem));
    frag.append(section);
  }
  if (!items.length) frag.append(el("p", "status", "이 호에는 항목이 없습니다"));
  main.replaceChildren(frag);
  document.title = `${issue.date} · 개발·AI 주간 소식`;
}

/** 해시에 맞는 호를 불러온다. 해시가 없거나 모르는 날짜면 최신 호를 연다. */
async function route() {
  if (!issues.length) return;
  const wanted = location.hash.slice(1);
  const date = issues.some((i) => i.date === wanted) ? wanted : issues[0].date;
  select.value = date;
  showStatus("불러오는 중");
  try {
    renderIssue(await getJSON(`issues/${date}.json`));
    window.scrollTo(0, 0);
  } catch (err) {
    showStatus(`이 호를 불러오지 못했습니다 (${err.message})`, true);
  }
}

/** 호 목록을 불러와 선택 상자를 채우고 첫 화면을 그린다. */
async function init() {
  try {
    const list = await getJSON("issues/index.json");
    issues = (Array.isArray(list) ? list : []).filter((i) => i && DATE_RE.test(i.date));
  } catch (err) {
    showStatus(`호 목록을 불러오지 못했습니다 (${err.message})`, true);
    return;
  }
  if (!issues.length) {
    showStatus("아직 게시된 호가 없습니다");
    return;
  }
  select.replaceChildren(
    ...issues.map((i) => {
      const opt = el("option", null, i.date);
      opt.value = i.date;
      return opt;
    })
  );
  select.disabled = issues.length < 2; // 호가 하나뿐이면 고를 것이 없다
  select.addEventListener("change", () => (location.hash = select.value));
  window.addEventListener("hashchange", route);
  route();
}

init();
