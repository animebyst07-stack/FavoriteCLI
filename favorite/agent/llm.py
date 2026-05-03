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
            body = {
                "model": model_name,
                "messages": messages,
            }
            r = req.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            return strip_thinking_blocks(data["choices"][0]["message"]["content"])

        if provider_name == "OpenRouter":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/animebyst07-stack/FavoriteCLI",
                "X-Title": "FavoriteCLI",
            }
            body = {
                "model": model_name,
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
            return strip_thinking_blocks(data["choices"][0]["message"]["content"])

        if provider_name == "FavoriteAPI":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            body: dict = {"messages": messages, "model": model_name}
            r = req.post(
                f"{cfg.favorite_api_base_url}/api/v1/chat",
                headers=headers,
                json=body,
                timeout=90,
            )
            r.raise_for_status()
            return strip_thinking_blocks(r.json()["choices"][0]["message"]["content"])
            
    except Exception as e:
        # Fallback to hardcoded logic if router fails or selected provider fails
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
            headers=headers,
            json=body,
            timeout=60,
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
                if not delta:
                    continue

                buffer += delta
                
                while buffer:
                    if not in_thinking:
                        if "<thinking" in buffer:
                            start_idx = buffer.find("<thinking")
                            # If we have "<thinking", we might need more to see if it's really <thinking>
                            # but usually chunks are big enough. If it's at the end, wait.
                            if ">" in buffer[start_idx:]:
                                end_tag_idx = buffer.find(">", start_idx) + 1
                                # Yield everything before <thinking>
                                if start_idx > 0:
                                    yield buffer[:start_idx]
                                # Move to thinking state
                                in_thinking = True
                                buffer = buffer[end_tag_idx:]
                            else:
                                # We have a partial tag at the end, yield what's before it and keep the rest
                                if start_idx > 0:
                                    yield buffer[:start_idx]
                                    buffer = buffer[start_idx:]
                                break
                        else:
                            # No <thinking> tag in buffer
                            yield buffer
                            buffer = ""
                    else:
                        if "</thinking>" in buffer:
                            end_idx = buffer.find("</thinking>") + len("</thinking>")
                            in_thinking = False
                            buffer = buffer[end_idx:]
                        elif "</thinking" in buffer:
                            # Partial end tag at the end, wait for more
                            break
                        else:
                            # Still in thinking, discard buffer
                            buffer = ""
                            break
