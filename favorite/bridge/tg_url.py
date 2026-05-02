"""
FavoriteCLI — bridge/tg_url.py
Читает актуальный URL FavoriteAPI из pinned_message в Telegram-чате.
FavoriteAPI пинит своё красивое уведомление; URL хранится в entities (text_link).
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional

_cache: dict = {"url": None, "ts": 0.0}
_TTL = 30.0  # секунд


def fetch_url(bot_token: str, chat_id: str) -> Optional[str]:
    """Возвращает URL из pinned_message.entities. Кеш 30 сек."""
    now = time.time()
    if _cache["url"] and now - _cache["ts"] < _TTL:
        return _cache["url"]
    url = _fetch_from_pinned(bot_token, chat_id)
    if url:
        _cache["url"] = url
        _cache["ts"] = now
    return url


def invalidate() -> None:
    """Сбросить кеш (вызывать перед повторным фетчем после ConnectionError)."""
    _cache["url"] = None
    _cache["ts"] = 0.0


def _fetch_from_pinned(bot_token: str, chat_id: str) -> Optional[str]:
    """getChat -> pinned_message.entities -> text_link с trycloudflare.com."""
    try:
        cid = _normalize(chat_id)
        payload = json.dumps({"chat_id": cid}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/getChat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not data.get("ok"):
            return None
        pinned = data["result"].get("pinned_message")
        if not pinned:
            return None
        # Ищем text_link entity — там хранится href из HTML-сообщения
        for entity in pinned.get("entities", []):
            if entity.get("type") == "text_link":
                url = entity.get("url", "")
                if url.startswith("http"):
                    return url
        # Fallback: plain-text "FAPI_URL:<url>"
        text = pinned.get("text", "")
        if text.startswith("FAPI_URL:"):
            return text[len("FAPI_URL:"):]
    except Exception:
        pass
    return None


def _normalize(raw: str):
    raw = str(raw).strip()
    try:
        return int(raw)
    except ValueError:
        return raw
