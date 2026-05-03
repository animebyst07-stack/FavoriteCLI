"""
favorite/agent/executor.py
Handles LLM response tags: STEP, SHELL_RAW, SHELL_BG, SLEEP,
WRITE_FAV, WRITE_CTX, GIT_PUSH, SKILL, CONTINUE, POLL, WRITE_PLAN.

Display rules (Claude Code aesthetic):
  STEP      → compact left-bordered dim block, no markdown noise
  SHELL_RAW → show command + max 6 lines output, rest summarized
  SHELL_BG  → show command only
  WRITE_*   → completely silent (just writes file)
  SKILL     → single-line header, results compact
  POLL      → interactive question block
"""
import subprocess
import time
import threading
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.markup import escape
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
    elif name == "CONTINUE":
        return _handle_continue(tag)
    elif name == "POLL":
        return _handle_poll(tag)
    elif name == "WRITE_PLAN":
        return _handle_write_plan(tag, ctx)
    elif name == "READ_FILE":
        return _handle_read_file(tag, ctx)
    elif name == "WRITE_FILE":
        return _handle_write_file(tag, ctx)
    elif name == "ASK_USER":
        return _handle_ask_user(tag)
    elif name == "SUB_AGENT":
        return _handle_sub_agent(tag, cfg)
    elif name == "THINK":
        return None  # THINK is silent
    elif name in ("ADD_TASK", "UPDATE_TASK", "COMPLETE_TASK", "LIST_TASKS"):
        return _handle_tasks(tag, ctx)
    return None


def _handle_step(tag: ParsedTag) -> None:
    """Compact left-bordered thinking block — not markdown, not noisy."""
    from ..ui.chat import print_step
    body = (tag.body or tag.args.get("msg", "")).strip()
    if body:
        print_step(body)


def _handle_shell(tag: ParsedTag, ctx: "CommandContext", background: bool) -> str | None:
    from ..ui.chat import print_shell_cmd, print_shell_output
    cmd = (tag.body or "").strip()
    if not cmd:
        return None

    print_shell_cmd(cmd)

    if background:
        threading.Thread(
            target=subprocess.run,
            args=(cmd,),
            kwargs={"shell": True, "cwd": ctx.workdir},
            daemon=True,
        ).start()
        return None

    try:
        result = subprocess.run(
            cmd, shell=True, cwd=ctx.workdir,
            capture_output=True, text=True, timeout=30,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        print_shell_output(out, err)
        combined = "\n".join(filter(None, [out, err]))
        return f"$ {cmd}\n{combined}" if combined else f"$ {cmd}\n(no output)"
    except subprocess.TimeoutExpired:
        console.print("  [dim #995555]timeout (30s)[/dim #995555]")
        return f"$ {cmd}\nERROR: timeout"
    except Exception as e:
        console.print(f"  [dim #995555]error: {escape(str(e))}[/dim #995555]")
        return f"$ {cmd}\nERROR: {e}"


def _handle_sleep(tag: ParsedTag) -> None:
    try:
        secs = float(tag.args.get("s", tag.body or "1"))
        secs = min(secs, 30.0)
        console.print(f"  [dim #666666]sleep {secs}s[/dim #666666]")
        time.sleep(secs)
    except (ValueError, TypeError):
        pass


def _handle_write_fav(tag: ParsedTag, ctx: "CommandContext") -> None:
    """Silent — just writes file."""
    body = (tag.body or "").strip()
    if not body:
        return
    try:
        from ..memory.favorite_md import FavoriteMd
        FavoriteMd().write(body)
    except Exception as e:
        console.print(f"  [dim #995555]WRITE_FAV: {escape(str(e))}[/dim #995555]")


def _handle_write_ctx(tag: ParsedTag, ctx: "CommandContext") -> None:
    """Silent — just writes file."""
    body = (tag.body or "").strip()
    if not body:
        return
    try:
        ctx_path = Path(ctx.workdir) / "context_summary.md"
        ctx_path.write_text(body, encoding="utf-8")
    except Exception as e:
        console.print(f"  [dim #995555]WRITE_CTX: {escape(str(e))}[/dim #995555]")


def _handle_git_push(tag: ParsedTag, ctx: "CommandContext", cfg) -> None:
    msg = tag.args.get("msg", tag.body or "auto: agent push").strip()
    console.print(f"  [dim #666666]git push: {escape(msg[:60])}[/dim #666666]")
    try:
        from ..github.auto_push import AutoPush
        ap = AutoPush(cfg)
        ap.push_workdir(ctx.workdir, commit_msg=msg)
        console.print("  [dim #666666]pushed[/dim #666666]")
    except Exception as e:
        console.print(f"  [dim #995555]GIT_PUSH: {escape(str(e))}[/dim #995555]")


def _handle_skill(tag: ParsedTag, ctx: "CommandContext", cfg) -> str | None:
    from ..ui.chat import print_skill_header
    skill_name = tag.args.get("name", "").lower()
    query = (tag.body or tag.args.get("q", "")).strip()
    if skill_name == "websearch":
        print_skill_header("websearch", query)
        return _run_websearch(query, cfg)
    if skill_name == "fetch":
        print_skill_header("fetch", query[:60])
        return _run_fetch(query)
    if skill_name in ("fs", "fstools"):
        op = tag.args.get("op", "read")
        path = tag.args.get("path", "")
        print_skill_header(f"fs:{op}", path)
        return _run_fs(tag, ctx)
    console.print(f"  [dim #666666]skill '{escape(skill_name)}' not found[/dim #666666]")
    return None


def _handle_continue(tag: ParsedTag) -> str:
    """
    ≪CONTINUE≫hint≪/CONTINUE≫
    Signals the agentic loop to call LLM again — no tool output needed.
    Use to split long responses across multiple turns.
    """
    body = (tag.body or "").strip()
    return body if body else "[continue]"


def _handle_poll(tag: ParsedTag) -> str | None:
    """
    ≪POLL≫
    Question text
    – Option A
    – Option B
    ≪/POLL≫
    Shows structured question, reads answer, returns it as tool output.
    """
    body = (tag.body or "").strip()
    if not body:
        return None

    lines = body.splitlines()
    question_parts: list[str] = []
    options: list[str] = []
    for line in lines:
        s = line.strip()
        if s.startswith("–") or s.startswith("-"):
            options.append(s.lstrip("–- ").strip())
        elif s:
            question_parts.append(s)

    console.print()
    console.print(f"  [bold #ff8c00]?[/bold #ff8c00] {escape(' '.join(question_parts))}")
    for i, opt in enumerate(options, 1):
        console.print(f"  [dim #888888]{i}. {escape(opt)}[/dim #888888]")

    try:
        answer = input("  → ").strip()
    except (EOFError, KeyboardInterrupt):
        return "[no answer]"

    return f"[answer: {escape(answer)}]"


def _handle_write_plan(tag: ParsedTag, ctx: "CommandContext") -> str | None:
    """
    ≪WRITE_PLAN≫plan content≪/WRITE_PLAN≫
    Saves plan to sessions/<session_id>/plan.txt. Shows one-line confirmation.
    """
    body = (tag.body or "").strip()
    if not body:
        return None
    try:
        plan_dir = Path(ctx.workdir) / "sessions" / ctx.session_id
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_path = plan_dir / "plan.txt"
        plan_path.write_text(body, encoding="utf-8")
        console.print(
            f"  [bold #ff8c00]>[/bold #ff8c00] [dim #666666]plan saved → "
            f"sessions/{ctx.session_id}/plan.txt[/dim #666666]"
        )
        return f"[plan saved: sessions/{ctx.session_id}/plan.txt]"
    except Exception as e:
        console.print(f"  [dim #995555]WRITE_PLAN: {escape(str(e))}[/dim #995555]")
        return f"WRITE_PLAN ERROR: {e}"


def _handle_read_file(tag: ParsedTag, ctx: "CommandContext") -> str:
    path_str = tag.args.get("path", "").strip()
    if not path_str:
        return "READ_FILE ERROR: Missing path argument"
    try:
        path = Path(ctx.workdir) / path_str
        if not path.exists():
            return f"READ_FILE ERROR: File not found: {path_str}"
        if not path.is_file():
            return f"READ_FILE ERROR: Path is not a file: {path_str}"
        content = path.read_text(encoding="utf-8")
        console.print(f"  [dim #666666]read file: {path_str}[/dim #666666]")
        return content
    except Exception as e:
        return f"READ_FILE ERROR: {e}"


def _handle_write_file(tag: ParsedTag, ctx: "CommandContext") -> str:
    path_str = tag.args.get("path", "").strip()
    content = tag.body or ""
    if not path_str:
        return "WRITE_FILE ERROR: Missing path argument"
    try:
        path = Path(ctx.workdir) / path_str
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        console.print(f"  [dim #666666]wrote file: {path_str}[/dim #666666]")
        return f"File saved: {path_str}"
    except Exception as e:
        return f"WRITE_FILE ERROR: {e}"


def _handle_ask_user(tag: ParsedTag) -> str:
    prompt_text = tag.args.get("text", "Question").strip()
    body = (tag.body or "").strip()
    display = f"{prompt_text}: {body}" if body else prompt_text
    
    console.print()
    console.print(f"  [bold #ff8c00]?[/bold #ff8c00] {escape(display)}")
    try:
        answer = input("  → ").strip()
        return f"[user answer]: {answer}"
    except (EOFError, KeyboardInterrupt):
        return "[no answer]"


def _handle_sub_agent(tag: ParsedTag, cfg) -> str:
    role = tag.args.get("role", "summarizer").strip()
    task = (tag.body or "").strip()
    if not task:
        return "SUB_AGENT ERROR: Missing task description in body"
    
    console.print(f"  [bold #ff8c00]●[/bold #ff8c00] [dim]Spawning sub-agent:[/dim] [cyan]{role}[/cyan]")
    
    try:
        from .sub_agent import run_sub_agent
        result = run_sub_agent(role, task, cfg)
        return f"[sub-agent {role} output]:\n{result}"
    except Exception as e:
        return f"SUB_AGENT ERROR: {e}"


def _handle_tasks(tag: ParsedTag, ctx: "CommandContext") -> str:
    from ..tasks.manager import TaskManager
    session_dir = Path(__file__).resolve().parent.parent.parent / "sessions" / ctx.session_id
    manager = TaskManager(session_dir)
    name = tag.name.upper()

    try:
        if name == "ADD_TASK":
            title = (tag.body or tag.args.get("title", "")).strip()
            if not title: return "ADD_TASK ERROR: Missing title"
            task = manager.add_task(title)
            console.print(f"  [dim #666666]task added: {task.id}[/dim #666666]")
            return f"Task added: {task.id}"
        
        elif name == "UPDATE_TASK":
            tid = tag.args.get("id", "").strip()
            status = tag.args.get("status", "").strip()
            if not tid: return "UPDATE_TASK ERROR: Missing id"
            kwargs = {}
            if status: kwargs["status"] = status
            if tag.body: kwargs["notes"] = tag.body.strip()
            task = manager.update_task(tid, **kwargs)
            if not task: return f"UPDATE_TASK ERROR: Task {tid} not found"
            console.print(f"  [dim #666666]task updated: {tid}[/dim #666666]")
            return f"Task {tid} updated"

        elif name == "COMPLETE_TASK":
            tid = (tag.body or tag.args.get("id", "")).strip()
            if not tid: return "COMPLETE_TASK ERROR: Missing id"
            task = manager.update_task(tid, status="done")
            if not task: return f"COMPLETE_TASK ERROR: Task {tid} not found"
            console.print(f"  [dim #666666]task completed: {tid}[/dim #666666]")
            return f"Task {tid} completed"

        elif name == "LIST_TASKS":
            tasks = manager.list_tasks()
            if not tasks: return "No tasks found"
            lines = [f"- [{t.id}] {t.status}: {t.title}" for t in tasks]
            return "\n".join(lines)
    except Exception as e:
        return f"{name} ERROR: {e}"
    return ""


def _run_websearch(query: str, cfg) -> str | None:
    if not query:
        return None
    try:
        from ..skills.web_search import search
        results = search(query, cfg)
        lines = []
        for r in results[:3]:
            console.print(
                f"  [dim #888888]{escape(r['title'][:70])}[/dim #888888]"
            )
            lines.append(f"[{r['title']}]({r['url']})\n{r['snippet']}")
        return "\n\n".join(lines) if lines else None
    except Exception as e:
        console.print(f"  [dim #995555]websearch: {escape(str(e))}[/dim #995555]")
        return f"WebSearch ERROR: {e}"


def _run_fetch(url: str) -> str | None:
    if not url:
        return None
    try:
        from ..skills.fetch_url import fetch_text
        text = fetch_text(url)
        # Don't print to screen — just return to AI
        return text[:4000]
    except Exception as e:
        console.print(f"  [dim #995555]fetch: {escape(str(e))}[/dim #995555]")
        return f"Fetch ERROR: {e}"


def _run_fs(tag: ParsedTag, ctx: "CommandContext") -> str | None:
    op = tag.args.get("op", "read")
    path = tag.args.get("path", "")
    try:
        from ..skills.fs_tools import fs_op
        result = fs_op(op, path, tag.body or "", ctx.workdir)
        # Don't print file contents to screen — just return to AI
        return result or None
    except Exception as e:
        console.print(f"  [dim #995555]fs: {escape(str(e))}[/dim #995555]")
        return f"FS ERROR: {e}"
