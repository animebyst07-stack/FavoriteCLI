"""
favorite/commands/reset_cmd.py
/reset — сброс контекста диалога через FavoriteAPI.
"""
from rich.console import Console
from rich.text import Text

from .base import ICommand, CommandContext
from ..ui.theme import ORANGE, GRAY

console = Console()


class ResetCommand(ICommand):
    name = "/reset"
    description = "Сбросить контекст диалога (очистить историю на сервере)"
    priority = 25

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config
        fav_key = cfg.default_favorite_key()
        if not fav_key:
            console.print(f"[bold red]FavoriteAPI не настроен.[/bold red] Добавь ключ через [bold {ORANGE}]/Favorite API[/bold {ORANGE}]")
            return

        from ..api.favorite_api import FavoriteApiClient
        base_url = getattr(cfg, "favorite_api_base_url", FavoriteApiClient.DEFAULT_BASE)
        client = FavoriteApiClient(
            api_key=fav_key.get("key", ""),
            base_url=base_url,
            model=fav_key.get("model"),
        )

        console.print(f"\n[bold {ORANGE}]●[/bold {ORANGE}] Сброс контекста...")

        try:
            result = client.reset_context()
        except Exception as e:
            console.print(f"[red]Ошибка соединения с FavoriteAPI: {e}[/red]")
            _wait()
            return

        # Сервер требует выбора (контекст переполнен — limit_hit)
        if result.get("requires_choice"):
            _handle_limit_hit(client, result)
            return

        # Обычный сброс — успех
        if result.get("reset"):
            if ctx.mgr and ctx.session_id:
                ctx.mgr.clear_history(ctx.session_id)
            console.print(f"[bold {ORANGE}]●[/bold {ORANGE}] [dim {GRAY}]Контекст сброшен. История диалога очищена локально и на сервере.[/dim {GRAY}]")
        else:
            err = result.get("error", "неизвестная ошибка")
            console.print(f"[red]Не удалось сбросить контекст: {err}[/red]")

        _wait()


def _handle_limit_hit(client, result: dict) -> None:
    """Контекст переполнен — спрашиваем что сохранить."""
    files = result.get("files", {})
    ctx_info = files.get("context", {})
    fav_info = files.get("favorite", {})

    console.print(f"\n[bold red]Контекст переполнен (~180KB).[/bold red] Выбери что сохранить:\n")

    # context.md
    if ctx_info.get("exists"):
        preview = (ctx_info.get("preview") or "")[:80]
        size = ctx_info.get("size_chars", 0)
        console.print(f"  [bold {ORANGE}]context.md[/bold {ORANGE}] ({size} символов)")
        if preview:
            console.print(f"  [dim]  {preview}...[/dim]")
    else:
        console.print(f"  [dim]context.md — пусто[/dim]")

    # Favorite.md
    if fav_info.get("exists"):
        preview = (fav_info.get("preview") or "")[:80]
        size = fav_info.get("size_chars", 0)
        console.print(f"  [bold {ORANGE}]Favorite.md[/bold {ORANGE}] ({size} символов)")
        if preview:
            console.print(f"  [dim]  {preview}...[/dim]")
    else:
        console.print(f"  [dim]Favorite.md — пусто[/dim]")

    console.print(f"""
  [bold]1.[/bold] Очистить всё (полный сброс)
  [bold]2.[/bold] Сохранить Favorite.md, очистить context
  [bold]3.[/bold] Сохранить оба файла
  [bold]4.[/bold] Отмена
""")

    while True:
        try:
            choice = input("  Выбери [1-4]: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("[dim]Отменено.[/dim]")
            return

        if choice == "1":
            ctx_action, fav_action = "clear", "clear"
            break
        elif choice == "2":
            ctx_action, fav_action = "clear", "keep"
            break
        elif choice == "3":
            ctx_action, fav_action = "keep", "keep"
            break
        elif choice == "4":
            console.print("[dim]Отменено.[/dim]")
            return
        else:
            console.print("  [dim]Введи 1, 2, 3 или 4[/dim]")

    try:
        apply_result = client.reset_context_apply(context=ctx_action, favorite=fav_action)
    except Exception as e:
        console.print(f"[red]Ошибка применения сброса: {e}[/red]")
        _wait()
        return

    if apply_result.get("reset"):
        if ctx.mgr and ctx.session_id:
            ctx.mgr.clear_history(ctx.session_id)
        action_label = {
            ("clear", "clear"): "Всё очищено",
            ("clear", "keep"): "context очищен, Favorite.md сохранён",
            ("keep", "keep"): "Оба файла сохранены, контекст сброшен",
        }.get((ctx_action, fav_action), "Сброс применён")
        console.print(f"[bold {ORANGE}]●[/bold {ORANGE}] [dim {GRAY}]{action_label}. Контекст сброшен.[/dim {GRAY}]")
    else:
        err = apply_result.get("error", "неизвестная ошибка")
        console.print(f"[red]Ошибка: {err}[/red]")

    _wait()


def _wait() -> None:
    try:
        input("\n  [Enter чтобы продолжить]")
    except (EOFError, KeyboardInterrupt):
        pass
