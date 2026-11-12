// 주간 소식 뷰어: issues/index.json으로 호 목록을 만들고, #YYYY-MM-DD 해시의 호를 그린다.
"use strict";

const CATEGORIES = [
  ["ai_research", "AI 연구"],
  ["ai_industry", "AI 업계"],
  ["dev", "개발"],
  ["kr", "국내"],
];
const SOURCE_NAMES = {
  hf_daily_papers: "HF Papers",
  anthropic_news: "Anthropic",
  openai_news: "OpenAI",
  deepmind_blog: "DeepMind",
  meta_ai_blog: "Meta AI",
  hacker_news: "Hacker News",
  github_trending: "GitHub Trending",
  geeknews: "GeekNews",
};
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

/** 2026-11-15 → 2026년 11월 15일 */
function formatDate(date) {
  const [y, m, d] = date.split("-").map(Number);
  return `${y}년 ${m}월 ${d}일`;
}

/** 항목 하나를 카드로 만든다. */
function renderItem(item) {
  const card = el("article", "item");
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
  card.append(h3);
  if (item.commentary) card.append(el("p", "commentary", item.commentary));

  const meta = el("p", "meta");
  const sources = [item.source, ...(item.also_seen_in || [])].filter(Boolean);
  for (const s of sources) meta.append(el("span", "badge", SOURCE_NAMES[s] || s));
  if (href) meta.append(el("span", "host", new URL(href).hostname.replace(/^www\./, "")));
  card.append(meta);
  return card;
}

/** 호 하나를 카테고리 섹션으로 나눠 그린다. */
function renderIssue(issue) {
  const frag = document.createDocumentFragment();
  const head = el("div", "issue-head");
  head.append(el("p", "date", formatDate(issue.date)), el("h2", null, issue.title));
  if (issue.intro) head.append(el("p", "intro", issue.intro));
  frag.append(head);

  const items = issue.items || [];
  const known = new Set(CATEGORIES.map(([key]) => key));
  const groups = [...CATEGORIES, ["_other", "기타"]];
  for (const [key, label] of groups) {
    const list = items.filter((i) => (key === "_other" ? !known.has(i.category) : i.category === key));
    if (!list.length) continue;
    const section = el("section", "category");
    const h = el("h2", "category-title", label);
    h.append(el("span", "count", String(list.length)));
    section.append(h, ...list.map(renderItem));
    frag.append(section);
  }
  if (!items.length) frag.append(el("p", "status", "이 호에는 항목이 없습니다."));
  main.replaceChildren(frag);
  document.title = `${issue.title} · 개발·AI 주간 소식`;
}

/** 해시에 맞는 호를 불러온다. 해시가 없거나 모르는 날짜면 최신 호를 연다. */
async function route() {
  if (!issues.length) return;
  const wanted = location.hash.slice(1);
  const date = issues.some((i) => i.date === wanted) ? wanted : issues[0].date;
  select.value = date;
  showStatus("불러오는 중…");
  try {
    renderIssue(await getJSON(`issues/${date}.json`));
    window.scrollTo(0, 0);
  } catch (err) {
    showStatus(`이 호를 불러오지 못했습니다. (${err.message})`, true);
  }
}

/** 호 목록을 불러와 선택 상자를 채우고 첫 화면을 그린다. */
async function init() {
  try {
    const list = await getJSON("issues/index.json");
    issues = (Array.isArray(list) ? list : []).filter((i) => i && DATE_RE.test(i.date));
  } catch (err) {
    showStatus(`호 목록을 불러오지 못했습니다. (${err.message})`, true);
    return;
  }
  if (!issues.length) {
    showStatus("아직 게시된 호가 없습니다.");
    return;
  }
  select.replaceChildren(
    ...issues.map((i) => {
      const opt = el("option", null, `${i.date}${i.count ? ` · ${i.count}개` : ""}`);
      opt.value = i.date;
      return opt;
    })
  );
  select.disabled = false;
  select.addEventListener("change", () => (location.hash = select.value));
  window.addEventListener("hashchange", route);
  route();
}

init();
