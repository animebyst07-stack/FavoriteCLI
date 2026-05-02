"""
favorite/agent/executor.py
Выполняет теги из ответа LLM: STEP, SHELL_RAW, SHELL_BG, SLEEP,
WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL.
"""
import subprocess
import time
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from .tags import ParsedTag

if TYPE_CHECKING:
    from ..commands.base import CommandContext

console = Console()


def execute_tags(tags: list[ParsedTag], ctx: "CommandContext", cfg) -> None:
    """Последовательно выполняет теги из ответа агента."""
    for tag in tags:
        _dispatch(tag, ctx, cfg)


def _dispatch(tag: ParsedTag, ctx: "CommandContext", cfg) -> None:
    name = tag.name.upper()
    if name == "STEP":
        _handle_step(tag)
    elif name == "SHELL_RAW":
        _handle_shell(tag, ctx, background=False)
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
        _handle_skill(tag, ctx, cfg)
    else:
        console.print(f"  [dim]Тег {tag.name} — не поддерживается.[/dim]")


def _handle_step(tag: ParsedTag) -> None:
    body = tag.body or tag.args.get("msg", "")
    if body:
        console.print(f"  [dim]→ {body}[/dim]")


def _handle_shell(tag: ParsedTag, ctx: "CommandContext", background: bool) -> None:
    cmd = (tag.body or "").strip()
    if not cmd:
        return
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
        else:
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
    except subprocess.TimeoutExpired:
        console.print("  [red]Превышен таймаут (30 сек).[/red]")
    except Exception as e:
        console.print(f"  [red]Ошибка shell: {e}[/red]")


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
        fmd = FavoriteMd(ctx.workdir)
        fmd.write(body)
        console.print("  [dim]Favorite.md обновлён.[/dim]")
    except Exception as e:
        console.print(f"  [red]WRITE_FAV: {e}[/red]")


def _handle_write_ctx(tag: ParsedTag, ctx: "CommandContext") -> None:
    body = (tag.body or "").strip()
    if not body:
        return
    try:
        ctx_path = Path(ctx.workdir) / "context_summary.md"
        ctx_path.write_text(body, encoding="utf-8")
        console.print("  [dim]context_summary.md записан.[/dim]")
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


def _handle_skill(tag: ParsedTag, ctx: "CommandContext", cfg) -> None:
    skill_name = tag.args.get("name", "").lower()
    query = (tag.body or tag.args.get("q", "")).strip()
    if skill_name == "websearch":
        _run_websearch(query, cfg)
    elif skill_name == "fetch":
        _run_fetch(query)
    elif skill_name in ("fs", "fstools"):
        _run_fs(tag, ctx)
    else:
        console.print(f"  [dim]Скилл '{skill_name}' не найден.[/dim]")


def _run_websearch(query: str, cfg) -> None:
    if not query:
        return
    try:
        from ..skills.web_search import search
        results = search(query, cfg)
        for r in results[:3]:
            console.print(f"  [bold #ff8c00]{r['title']}[/bold #ff8c00]")
            console.print(f"  [dim]{r['snippet']}[/dim]")
            console.print(f"  [blue]{r['url']}[/blue]\n")
    except Exception as e:
        console.print(f"  [red]WebSearch: {e}[/red]")


def _run_fetch(url: str) -> None:
    if not url:
        return
    try:
        from ..skills.fetch_url import fetch_text
        text = fetch_text(url)
        console.print(f"  [dim]{text[:1500]}[/dim]")
    except Exception as e:
        console.print(f"  [red]Fetch: {e}[/red]")


def _run_fs(tag: ParsedTag, ctx: "CommandContext") -> None:
    op = tag.args.get("op", "read")
    path = tag.args.get("path", "")
    try:
        from ..skills.fs_tools import fs_op
        result = fs_op(op, path, tag.body or "", ctx.workdir)
        if result:
            console.print(f"  [dim]{result[:2000]}[/dim]")
    except Exception as e:
        console.print(f"  [red]FS: {e}[/red]")
