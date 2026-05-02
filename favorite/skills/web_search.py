"""
favorite/skills/web_search.py
WebSearch скилл: VoidAI perplexity/sonar → DuckDuckGo HTML fallback.
"""
import json
import re
import urllib.request
import urllib.parse
from typing import Optional


def search(query: str, cfg) -> list[dict]:
    """Возвращает список {"title", "snippet", "url"}. До 5 результатов."""
    results = _void_ai_search(query, cfg)
    if results:
        return results
    return _ddg_fallback(query)


def _void_ai_search(query: str, cfg) -> list[dict]:
    """VoidAI через OpenRouter-совместимый API (perplexity/sonar)."""
    try:
        void_key = getattr(cfg, "voidai_key", None) or ""
        if not void_key:
            or_key = cfg.default_openrouter_key()
            if or_key:
                void_key = or_key.get("key", "")
        if not void_key:
            return []

        payload = json.dumps({
            "model": "perplexity/sonar",
            "messages": [{"role": "user", "content": f"Search: {query}"}],
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {void_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
                "X-Title": "FavoriteCLI",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return [{"title": "VoidAI/Sonar", "snippet": content[:800], "url": ""}]
    except Exception:
        return []


def _ddg_fallback(query: str) -> list[dict]:
    """DuckDuckGo HTML scrape — без JS, без API-ключа."""
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FavoriteCLI/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        results = []
        for m in re.finditer(
            r'class="result__title"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'class="result__snippet"[^>]*>(.*?)</span>',
            html, re.DOTALL
        ):
            url_raw = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", m.group(3)).strip()
            results.append({"title": title, "snippet": snippet, "url": url_raw})
            if len(results) >= 5:
                break
        return results
    except Exception:
        return []
