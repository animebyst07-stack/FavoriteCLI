"""
Мастер первоначальной настройки FavoriteCLI.
Запускается автоматически если нет ни одного API-ключа.
"""
from rich.console import Console
from rich.panel import Panel

console = Console()

_ORANGE = "bold #ff8c00"
_GRAY   = "dim"
_LINE   = "\u2500" * 54


def _ask(prompt: str, required: bool = False, secret: bool = False) -> str:
    while True:
        try:
            val = input(f"  {prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            return ""
        if val or not required:
            return val
        console.print("  [red]Поле обязательно. Попробуй ещё раз.[/red]")


def run_setup(cfg) -> bool:
    """
    Интерактивный мастер настройки.
    Возвращает True если минимальная конфигурация задана.
    """
    console.print()
    console.print(Panel(
        "[bold #ff8c00]Добро пожаловать в FavoriteCLI![/bold #ff8c00]\n\n"
        "[dim]Ключи API не найдены. Давай настроим всё за пару минут.\n"
        "Данные сохраняются локально в [/dim][white]config/[/white][dim] и никуда не отправляются.[/dim]",
        border_style="#ff8c00",
        expand=False,
        width=58,
    ))
    console.print()

    # --- OpenRouter (основной провайдер) ---
    console.print(f"[{_ORANGE}]1. OpenRouter API[/{_ORANGE}]")
    console.print(f"[{_GRAY}]   Получить ключ: https://openrouter.ai → Keys[/{_GRAY}]")
    console.print(f"[{_GRAY}]   Формат: sk-or-v1-...[/{_GRAY}]")
    or_key = _ask("Вставь ключ OpenRouter (Enter — пропустить)")
    if or_key:
        model = _ask("Модель по умолчанию [qwen/qwen3-coder:free]") or "qwen/qwen3-coder:free"
        cfg.add_openrouter_key(or_key, label="default", model=model)
        console.print(f"  [green]OpenRouter добавлен.[/green]")
    else:
        console.print(f"  [{_GRAY}]Пропущено.[/{_GRAY}]")

    console.print()

    # --- FavoriteAPI ---
    console.print(f"[{_ORANGE}]2. FavoriteAPI[/{_ORANGE}]")
    console.print(f"[{_GRAY}]   Локальный прокси к Gemini (запускается отдельно).[/{_GRAY}]")
    console.print(f"[{_GRAY}]   Ключ вида: fa_sk_...[/{_GRAY}]")
    fav_key = _ask("Вставь ключ FavoriteAPI (Enter — пропустить)")
    if fav_key:
        base_url = _ask("Адрес сервера [http://127.0.0.1:5005]") or "http://127.0.0.1:5005"
        cfg.set_favorite_api_base_url(base_url)
        cfg.add_favorite_key(fav_key, label="default")
        console.print(f"  [green]FavoriteAPI добавлен.[/green]")
    else:
        console.print(f"  [{_GRAY}]Пропущено.[/{_GRAY}]")

    console.print()

    # --- VoidAI (WebSearch) ---
    console.print(f"[{_ORANGE}]3. VoidAI (для скилла WebSearch)[/{_ORANGE}]")
    console.print(f"[{_GRAY}]   Ключ вида: sk-va-unified-...[/{_GRAY}]")
    void_key = _ask("Вставь ключ VoidAI (Enter — пропустить)")
    if void_key:
        cfg.set_void_ai_key(void_key)
        console.print(f"  [green]VoidAI добавлен.[/green]")
    else:
        console.print(f"  [{_GRAY}]Пропущено. Поиск будет через DuckDuckGo.[/{_GRAY}]")

    console.print()

    # --- GitHub (для авто-пуша) ---
    console.print(f"[{_ORANGE}]4. GitHub (для авто-пуша кода)[/{_ORANGE}]")
    console.print(f"[{_GRAY}]   Нужен PAT с правом repo. Получить: github.com → Settings → Tokens[/{_GRAY}]")
    gh_token = _ask("Вставь GitHub токен (Enter — пропустить)")
    if gh_token:
        gh_owner = _ask("GitHub логин (username)")
        gh_repo  = _ask("Репозиторий [FavoriteCLI]") or "FavoriteCLI"
        if gh_owner:
            cfg.set_github(token=gh_token, owner=gh_owner, repo=gh_repo)
            console.print(f"  [green]GitHub настроен: {gh_owner}/{gh_repo}[/green]")
        else:
            console.print(f"  [red]Логин не указан, GitHub не сохранён.[/red]")
    else:
        console.print(f"  [{_GRAY}]Пропущено. Авто-пуш недоступен.[/{_GRAY}]")

    console.print()

    if not cfg.has_any_provider():
        console.print(
            "[red]Ни одного провайдера не добавлено.[/red]\n"
            "[dim]Добавь ключи через /Favorite API или /OpenRouter API в любой момент.[/dim]"
        )
        return False

    console.print(f"[{_ORANGE}]Настройка завершена![/{_ORANGE}] Запускаю FavoriteCLI...\n")
    return True
