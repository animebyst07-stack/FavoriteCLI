"""
Tag parser for FavoriteCLI.

Parses ≪TAG≫ / ≪TAG:args≫ / ≪TAG≫...≪/TAG≫ patterns from LLM output.
"""
import re
from dataclasses import dataclass
from typing import Any

TAG_OPEN  = "\u226a"   # ≪
TAG_CLOSE = "\u226b"   # ≫
TAG_SLASH = "/"

BLOCK_RE = re.compile(
    rf"{re.escape(TAG_OPEN)}(\w+)(?::([^{re.escape(TAG_CLOSE)}]*?))?{re.escape(TAG_CLOSE)}"
    rf"(.*?)"
    rf"{re.escape(TAG_OPEN)}/\1{re.escape(TAG_CLOSE)}",
    re.DOTALL,
)
INLINE_RE = re.compile(
    rf"{re.escape(TAG_OPEN)}(\w+)(?::([^{re.escape(TAG_CLOSE)}]*?))?{re.escape(TAG_CLOSE)}"
)


@dataclass
class ParsedTag:
    name: str
    args: dict[str, str]
    body: str | None
    span: tuple[int, int]


def _parse_args(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    result: dict[str, str] = {}
    for part in raw.split(":"):
        if "=" in part:
            k, _, v = part.partition("=")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def extract_tags(text: str) -> list[ParsedTag]:
    tags: list[ParsedTag] = []
    consumed: set[tuple[int,int]] = set()

    for m in BLOCK_RE.finditer(text):
        pt = ParsedTag(
            name=m.group(1),
            args=_parse_args(m.group(2)),
            body=m.group(3).strip(),
            span=(m.start(), m.end()),
        )
        tags.append(pt)
        consumed.add((m.start(), m.end()))

    for m in INLINE_RE.finditer(text):
        span = (m.start(), m.end())
        if any(s <= span[0] < e for s, e in consumed):
            continue
        name = m.group(1)
        if name.startswith("/"):
            continue
        pt = ParsedTag(
            name=name,
            args=_parse_args(m.group(2)),
            body=None,
            span=span,
        )
        tags.append(pt)

    tags.sort(key=lambda t: t.span[0])
    return tags


def strip_tags(text: str) -> str:
    result = BLOCK_RE.sub("", text)
    result = INLINE_RE.sub("", result)
    return result.strip()
