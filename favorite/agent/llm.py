"""
favorite/agent/llm.py
LLM call helpers: blocking call + SSE streaming (OpenRouter only).
"""
from __future__ import annotations

import json
from typing import Iterator


def call_llm(messages: list[dict], cfg) -> str:
    """Blocking LLM call. Returns full response text."""
    import requests as req

    or_key = cfg.default_openrouter_key()
    if or_key:
        headers = {
            "Authorization": f"Bearer {or_key['key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
            "X-Title": "FavoriteCLI",
        }
        body = {
            "model": or_key.get("model", "qwen/qwen3-coder:free"),
            "messages": messages,
        }
        r = req.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=60,
        )
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return data["choices"][0]["message"]["content"]

    fav = cfg.default_favorite_key()
    if fav:
        headers = {
            "Authorization": f"Bearer {fav['key']}",
            "Content-Type": "application/json",
        }
        body: dict = {"messages": messages}
        if fav.get("model"):
            body["model"] = fav["model"]
        r = req.post(
            f"{cfg.favorite_api_base_url}/api/v1/chat",
            headers=headers,
            json=body,
            timeout=90,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    raise RuntimeError("Нет доступного провайдера.")


def stream_llm(messages: list[dict], cfg) -> Iterator[str]:
    """
    SSE streaming for OpenRouter only.
    Yields text chunks as they arrive.
    Raises RuntimeError if OpenRouter key not configured — caller should fallback.
    """
    import requests as req

    or_key = cfg.default_openrouter_key()
    if not or_key:
        raise RuntimeError("stream_llm: OpenRouter ключ не найден")

    headers = {
        "Authorization": f"Bearer {or_key['key']}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
        "X-Title": "FavoriteCLI",
    }
    body = {
        "model": or_key.get("model", "qwen/qwen3-coder:free"),
        "messages": messages,
        "stream": True,
    }
    with req.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
        stream=True,
        timeout=90,
    ) as r:
        r.raise_for_status()
        for raw_line in r.iter_lines():
            if not raw_line:
                continue
            if raw_line == b"data: [DONE]":
                break
            if raw_line.startswith(b"data: "):
                try:
                    data = json.loads(raw_line[6:])
                except json.JSONDecodeError:
                    continue
                delta = (
                    data.get("choices", [{}])[0]
                    .get("delta", {})
                    .get("content", "")
                )
                if delta:
                    yield delta
