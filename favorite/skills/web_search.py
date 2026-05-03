"""
favorite/skills/web_search.py
WebSearch скилл: VoidAI perplexity/sonar → DuckDuckGo HTML fallback.
Возвращает список результатов с реальным содержимым (не только заголовки).
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
        void_key = getattr(cfg, 'voidai_key', None) or ''
        if not void_key:
            or_key = cfg.default_openrouter_key()
            if or_key:
                void_key = or_key.get('key', '')
        if not void_key:
            return []

        # Prompt явно запрашивает конкретные актуальные данные с числами и источниками
        system_msg = (
            'You are a real-time web search assistant. '
            'Always provide EXACT current numbers, prices, rates, dates from live sources. '
            'Do NOT say approximate values. Do NOT make up numbers. '
            'Always cite the source URL for each fact.'
        )
        user_msg = (
            f'{query}

'
            'Provide EXACT current values with numbers. '
            'Format each fact as: [VALUE] — source: [URL]'
        )

        payload = json.dumps({
            'model': 'perplexity/sonar',
            'messages': [
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': user_msg},
            ],
        }).encode('utf-8')
        req = urllib.request.Request(
            'https://openrouter.ai/api/v1/chat/completions',
            data=payload,
            headers={
                'Authorization': f'Bearer {void_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/animebyst07-stack/FavoriteCLI',
                'X-Title': 'FavoriteCLI',
            },
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        content = data['choices'][0]['message']['content']
        if not content or len(content) < 20:
            return []
        return [{'title': 'VoidAI/Sonar (live search)', 'snippet': content[:3000], 'url': ''}]
    except Exception:
        return []


def _ddg_fallback(query: str) -> list[dict]:
    """DuckDuckGo HTML scrape — без JS, без API-ключа."""
    try:
        q = urllib.parse.quote_plus(query)
        url = f'https://html.duckduckgo.com/html/?q={q}'
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='replace')

        results = []

        # Извлекаем блоки результатов
        blocks = re.findall(
            r'<div[^>]+class="[^"]*result[^"]*"[^>]*>(.*?)</div>s*</div>',
            html, re.DOTALL
        )

        for block in blocks:
            # URL
            url_match = re.search(r'href="(https?://[^"]+)"', block)
            raw_url = url_match.group(1) if url_match else ''
            # Пропускаем DDG-служебные ссылки
            if 'duckduckgo.com' in raw_url:
                continue

            # Заголовок — ищем в тегах a, h2
            title_match = re.search(r'<(?:a|h2)[^>]*>(.*?)</(?:a|h2)>', block, re.DOTALL)
            title = _clean(title_match.group(1)) if title_match else ''

            # Сниппет — ищем класс result__snippet или просто весь текст блока
            snip_match = re.search(r'class="[^"]*snippet[^"]*"[^>]*>(.*?)</(?:div|span|a)>', block, re.DOTALL)
            if snip_match:
                snippet = _clean(snip_match.group(1))
            else:
                # Взять весь текст блока как сниппет
                snippet = _clean(block)[:500]

            if not title and not snippet:
                continue

            results.append({'title': title[:200], 'snippet': snippet[:600], 'url': raw_url})
            if len(results) >= 5:
                break

        return results
    except Exception:
        return []


def _clean(html: str) -> str:
    """Убирает HTML-теги и нормализует пробелы."""
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&#x27;|&quot;', "'", text)
    text = re.sub(r'[ 	]+', ' ', text)
    text = re.sub(r'
{2,}', '
', text)
    return text.strip()
