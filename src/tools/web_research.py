from typing import List

import requests


WIKIPEDIA_SEARCH_URL = "https://en.wikipedia.org/w/rest.php/v1/search/title"
WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def _clean_query(query: str) -> str:
    q = (query or "").strip()
    if "football" not in q.lower() and "soccer" not in q.lower():
        q = f"{q} football"
    return q


def _summarize_results(items: List[dict]) -> str:
    if not items:
        return "No web result found."
    lines = []
    for i, item in enumerate(items[:3], start=1):
        title = item.get("title", "Unknown")
        excerpt = item.get("excerpt", "")
        excerpt = excerpt.replace("<mark>", "").replace("</mark>", "")
        lines.append(f"{i}. {title}: {excerpt}")
    return "\n".join(lines)


def web_search_wikipedia(query: str) -> str:
    q = _clean_query(query)
    if not q:
        return "Please provide a query."

    try:
        response = requests.get(
            WIKIPEDIA_SEARCH_URL,
            params={"q": q, "limit": 5},
            timeout=10,
            headers={"User-Agent": "lab-react-football/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        pages = payload.get("pages", [])
        return _summarize_results(pages)
    except Exception as exc:
        return f"Web search failed: {exc}"


def web_page_summary(title: str) -> str:
    clean_title = (title or "").strip().replace(" ", "_")
    if not clean_title:
        return "Please provide a page title."

    try:
        response = requests.get(
            WIKIPEDIA_SUMMARY_URL.format(title=clean_title),
            timeout=10,
            headers={"User-Agent": "lab-react-football/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        summary = payload.get("extract", "")
        if not summary:
            return "No summary found."
        return f"{payload.get('title', clean_title)}: {summary}"
    except Exception as exc:
        return f"Web summary failed: {exc}"
