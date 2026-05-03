"""
favorite/agent/llm.py
LLM call helpers: blocking call + SSE streaming (OpenRouter only).
"""
from __future__ import annotations

import json
from typing import Iterator


def _inject_system_into_messages(messages: list[dict]) -> list[dict]:
    """
    FavoriteAPI and some Gemini-based APIs do NOT support role='system'.
    Extracts system messages and prepends their content to the first user message.
    """
    system_parts: list[str] = []
    other: list[dict] = []
    for msg in messages:
        if msg.get("role") == "system":
            system_parts.append(msg["content"])
        else:
            other.append(dict(msg))

    if not system_parts or not other:
        return messages

    system_text = "\n\n".join(system_parts)

    for i, msg in enumerate(other):
        if msg.get("role") == "user":
            other[i] = {
                "role": "user",
                "content": f"[SYSTEM INSTRUCTIONS]\n{system_text}\n\n[USER MESSAGE]\n{msg['content']}",
            }
            break
    else:
        other.insert(0, {"role": "user", "content": f"[SYSTEM INSTRUCTIONS]\n{system_text}"})

    # BUG FIX 5: If history is long, inject a reminder into the LAST message
    if len(other) >= 10:
        last_msg = other[-1]
        if last_msg.get("role") == "user":
            # Find workdir from system_text if possible, or just use a generic reminder
            import re
            workdir_match = re.search(r"Working directory: (.*)", system_text)
            workdir = workdir_match.group(1) if workdir_match else "unknown"
            
            reminder = f"\n\n[SYSTEM REMINDER: You are Favorite CLI agent. Working dir: {workdir}]"
            if reminder not in last_msg["content"]:
                last_msg["content"] += reminder

    return other


def _build_favoriteapi_body(messages: list[dict], cfg) -> dict:
    """
    Build request body for FavoriteAPI.
    - Injects system prompt into user message (Gemini doesn't support role=system)
    - Only sends 'model' field if user explicitly configured one — never uses router defaults
    """
    processed = _inject_system_into_messages(messages)
    body: dict = {"messages": processed}
    fav = cfg.default_favorite_key()
    if fav and fav.get("model"):
        body["model"] = fav["model"]
    return body


def call_llm(messages: list[dict], cfg) -> str:
    """Blocking LLM call. Returns full response text."""
    import requests as req
    from .response_processor import strip_thinking_blocks
    from .model_router import RouterModule

    prompt = messages[-1]["content"] if messages else ""

    try:
        provider_name, model_name, api_key = RouterModule.select_model(prompt, cfg)

        if provider_name == "NVIDIA":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = {"model": model_name, "messages": messages}
            r = req.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers, json=body, timeout=60,
            )
            r.raise_for_status()
            return strip_thinking_blocks(r.json()["choices"][0]["message"]["content"])

        if provider_name == "OpenRouter":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
                "X-Title": "FavoriteCLI",
            }
            body = {"model": model_name, "messages": messages}
            r = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers, json=body, timeout=60,
            )
            data = r.json()
            if "error" in data:
                raise RuntimeError(data["error"].get("message", str(data["error"])))
            return strip_thinking_blocks(data["choices"][0]["message"]["content"])

        if provider_name == "FavoriteAPI":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body = _build_favoriteapi_body(messages, cfg)
            r = req.post(
                f"{cfg.favorite_api_base_url}/api/v1/chat",
                headers=headers, json=body, timeout=90,
            )
            r.raise_for_status()
            return strip_thinking_blocks(r.json()["choices"][0]["message"]["content"])

    except Exception:
        pass

    # --- FALLBACK ---
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
            headers=headers, json=body, timeout=60,
        )
        data = r.json()
        if "error" in data:
            raise RuntimeError(data["error"].get("message", str(data["error"])))
        return strip_thinking_blocks(data["choices"][0]["message"]["content"])

    fav = cfg.default_favorite_key()
    if fav:
        headers = {
            "Authorization": f"Bearer {fav['key']}",
            "Content-Type": "application/json",
        }
        body = _build_favoriteapi_body(messages, cfg)
        r = req.post(
            f"{cfg.favorite_api_base_url}/api/v1/chat",
            headers=headers, json=body, timeout=90,
        )
        r.raise_for_status()
        return strip_thinking_blocks(r.json()["choices"][0]["message"]["content"])

    raise RuntimeError("Нет доступного провайдера.")


def stream_llm(messages: list[dict], cfg) -> Iterator[str]:
    """
    SSE streaming for OpenRouter only.
    Yields text chunks as they arrive, suppressing <thinking> blocks.
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

    in_thinking = False
    buffer = ""

    with req.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers, json=body, stream=True, timeout=90,
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
                if not delta:
                    continue

                buffer += delta

                while buffer:
                    if not in_thinking:
                        if "<thinking" in buffer:
                            start_idx = buffer.find("<thinking")
                            if ">" in buffer[start_idx:]:
                                end_tag_idx = buffer.find(">", start_idx) + 1
                                if start_idx > 0:
                                    yield buffer[:start_idx]
                                in_thinking = True
                                buffer = buffer[end_tag_idx:]
                            else:
                                if start_idx > 0:
                                    yield buffer[:start_idx]
                                    buffer = buffer[start_idx:]
                                break
                        else:
                            yield buffer
                            buffer = ""
                    else:
                        if "</thinking>" in buffer:
                            end_idx = buffer.find("</thinking>") + len("</thinking>")
                            in_thinking = False
                            buffer = buffer[end_idx:]
                        elif "</thinking" in buffer:
                            break
                        else:
                            buffer = ""
                            break
