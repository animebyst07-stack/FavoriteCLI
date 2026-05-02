"""
favorite/agent/executor.py
Handles LLM response tags: STEP, SHELL_RAW, SHELL_BG, SLEEP,
WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL.
Returns shell/skill output so app.py can feed it back to the AI.
"""
import subprocess
import time
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from .tags import ParsedTag

if TYPE_CHECKING:
    from ..commands.base import CommandContext

console = Console()


def execute_tags(tags: list[ParsedTag], ctx: "CommandContext", cfg) -> None:
    execute_tags_with_output(tags, ctx, cfg)


def execute_tags_with_output(tags: list[ParsedTag], ctx: "CommandContext", cfg) -> str:
    parts: list[str] = []
    for tag in tags:
        out = _dispatch(tag, ctx, cfg)
        if out:
            parts.append(out)
    return "\n".join(parts)


def _dispatch(tag: ParsedTag, ctx: "CommandContext", cfg) -> str | None:
    name = tag.name.upper()
    if name == "STEP":
        _handle_step(tag)
    elif name == "SHELL_RAW":
        return _handle_shell(tag, ctx, background=False)
    elif name == "SHELL_BG":
        _handle_shell(tag, ctx, background=True)
    elif name == "SLEEP":
        _handle_sleep(tag)
    elif name == "WRITE_FAV":
        _handle_write_fav(tag, ctx)
    elif name == "WRITE_CTX":
        _handle_write_ctx(tag, ctx)
    elif name == "GIT_PUSH":
        _handle_git_push(tag, ctx, cfg)
    elif name == "SKILL":
        return _handle_skill(tag, ctx, cfg)
    return None


def _handle_step(tag: ParsedTag) -> None:
    body = (tag.body or tag.args.get("msg", "")).strip()
    if body:
        console.print(Markdown(body), style="dim")


def _handle_shell(tag: ParsedTag, ctx: "CommandContext", background: bool) -> str | None:
    cmd = (tag.body or "").strip()
    if not cmd:
        return None
    console.print(f"  [#ff8c00]$ {cmd}[/#ff8c00]")
    try:
        if background:
            threading.Thread(
                target=subprocess.run,
                args=(cmd,),
                kwargs={"shell": True, "cwd": ctx.workdir},
                daemon=True,
            ).start()
            console.print("  [dim](фон)[/dim]")
            return None
        result = subprocess.run(
            cmd, shell=True, cwd=ctx.workdir,
            capture_output=True, text=True, timeout=30,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        if out:
            console.print(f"  [dim]{out[:2000]}[/dim]")
        if err:
            console.print(f"  [red]{err[:500]}[/red]")
        combined = "\n".join(filter(None, [out, err]))
        return f"$ {cmd}\n{combined}" if combined else None
    except subprocess.TimeoutExpired:
        console.print("  [red]Превышен таймаут (30 сек).[/red]")
        return f"$ {cmd}\nERROR: timeout"
    except Exception as e:
        console.print(f"  [red]Ошибка shell: {e}[/red]")
        return f"$ {cmd}\nERROR: {e}"


def _handle_sleep(tag: ParsedTag) -> None:
    try:
        secs = float(tag.args.get("s", tag.body or "1"))
        secs = min(secs, 30.0)
        console.print(f"  [dim]Жду {secs}с...[/dim]")
        time.sleep(secs)
    except (ValueError, TypeError):
        pass


def _handle_write_fav(tag: ParsedTag, ctx: "CommandContext") -> None:
    body = (tag.body or "").strip()
    if not body:
        return
    try:
        from ..memory.favorite_md import FavoriteMd
        FavoriteMd().write(body)
    except Exception as e:
        console.print(f"  [red]WRITE_FAV: {e}[/red]")


def _handle_write_ctx(tag: ParsedTag, ctx: "CommandContext") -> None:
    body = (tag.body or "").strip()
    if not body:
        return
    try:
        ctx_path = Path(ctx.workdir) / "context_summary.md"
        ctx_path.write_text(body, encoding="utf-8")
    except Exception as e:
        console.print(f"  [red]WRITE_CTX: {e}[/red]")


def _handle_git_push(tag: ParsedTag, ctx: "CommandContext", cfg) -> None:
    msg = tag.args.get("msg", tag.body or "auto: agent push").strip()
    console.print(f"  [dim]GIT_PUSH: {msg}[/dim]")
    try:
        from ..github.auto_push import AutoPush
        ap = AutoPush(cfg)
        ap.push_workdir(ctx.workdir, commit_msg=msg)
        console.print("  [dim]Запушено.[/dim]")
    except Exception as e:
        console.print(f"  [red]GIT_PUSH: {e}[/red]")


def _handle_skill(tag: ParsedTag, ctx: "CommandContext", cfg) -> str | None:
    skill_name = tag.args.get("name", "").lower()
    query = (tag.body or tag.args.get("q", "")).strip()
    if skill_name == "websearch":
        return _run_websearch(query, cfg)
    if skill_name == "fetch":
        return _run_fetch(query)
    if skill_name in ("fs", "fstools"):
        return _run_fs(tag, ctx)
    console.print(f"  [dim]Скилл '{skill_name}' не найден.[/dim]")
    return None


def _run_websearch(query: str, cfg) -> str | None:
    if not query:
        return None
    try:
        from ..skills.web_search import search
        results = search(query, cfg)
        lines = []
        for r in results[:3]:
            console.print(f"  [bold #ff8c00]{r['title']}[/bold #ff8c00]")
            console.print(f"  [dim]{r['snippet']}[/dim]")
            console.print(f"  [blue]{r['url']}[/blue]\n")
            lines.append(f"[{r['title']}]({r['url']})\n{r['snippet']}")
        return "\n\n".join(lines) if lines else None
    except Exception as e:
        console.print(f"  [red]WebSearch: {e}[/red]")
        return f"WebSearch ERROR: {e}"


def _run_fetch(url: str) -> str | None:
    if not url:
        return None
    try:
        from ..skills.fetch_url import fetch_text
        text = fetch_text(url)
        console.print(f"  [dim]{text[:1500]}[/dim]")
        return text[:4000]
    except Exception as e:
        console.print(f"  [red]Fetch: {e}[/red]")
        return f"Fetch ERROR: {e}"


def _run_fs(tag: ParsedTag, ctx: "CommandContext") -> str | None:
    op = tag.args.get("op", "read")
    path = tag.args.get("path", "")
    try:
        from ..skills.fs_tools import fs_op
        result = fs_op(op, path, tag.body or "", ctx.workdir)
        if result:
            console.print(f"  [dim]{result[:2000]}[/dim]")
        return result or None
    except Exception as e:
        console.print(f"  [red]FS: {e}[/red]")
        return f"FS ERROR: {e}"
