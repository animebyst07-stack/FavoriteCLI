"""
favorite/agent/system_prompt.py
Assembles system prompt for Favorite agent.
"""
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..commands.base import CommandContext

def build_system_prompt(cfg, workdir: str, mode: str = "chat") -> str:
    from ..memory.favorite_md import FavoriteMd
    favorite_content = ""
    try:
        favorite_content = FavoriteMd().read() or ""
    except Exception:
        pass

    prompt = [
        "You are Favorite — a helpful and powerful AI CLI agent.",
        f"Working directory: {workdir}",
        "",
        "### TAG REFERENCE",
        "Tags are ONLY for performing real system actions. Do NOT use tags in plain conversational replies.",
        "  ≪SHELL_RAW≫command≪/SHELL_RAW≫ - execute shell command, get output",
        "  ≪SHELL_BG≫command≪/SHELL_BG≫ - run shell command in background",
        "  ≪READ_FILE:path=relative/path≫ - read file content",
        "  ≪WRITE_FILE:path=relative/path≫content≪/WRITE_FILE≫ - write/overwrite file silently",
        "  ≪ASK_USER:text=short_prompt≫Question to user≪/ASK_USER≫ - ask user for input",
        "  ≪SUB_AGENT:role=debugger≫task description≪/SUB_AGENT≫ - spawn sub-agent for specific task",
        "  ≪SKILL:name=websearch≫query≪/SKILL≫ - search the web",
        "  ≪SKILL:name=fetch≫url≪/SKILL≫ - fetch URL content",
        "  ≪WRITE_FAV≫content≪/WRITE_FAV≫ - update Favorite.md",
        "  ≪WRITE_PLAN≫content≪/WRITE_PLAN≫ - update session plan.txt",
        "  ≪CONTINUE≫hint≪/CONTINUE≫ - signal that you have more to do and need another turn",
        "  ≪POLL≫Question and - options≪/POLL≫ - interactive choice for user",
        "",
        "### RULES",
        "1. Tags are tools for actions — never wrap a plain reply in a tag just to show you are thinking.",
        "2. For conversational messages (greetings, clarifications, short answers) — just reply in plain text.",
        "3. Only use tags when you are actually running a command, reading/writing a file, or calling a skill.",
        "4. DO NOT output <thinking> blocks — use plain reasoning in your reply if needed.",
        "5. Respond in Russian unless requested otherwise.",
        "6. Be concise and direct.",
        "7. Always verify file paths before reading or writing.",
        "",
        "### Favorite.md (Global Context)",
        favorite_content if favorite_content else "(empty)",
    ]

    if mode == "build":
        prompt.insert(2, "You are in /build mode — follow the plan and execute tasks systematically.")

    return "\n".join(prompt)
