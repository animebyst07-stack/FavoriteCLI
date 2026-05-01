from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info

# Список моделей: (display_name, model_id, ctx_k, free)
_CURATED_MODELS = [
    ("Qwen3 Coder",               "qwen/qwen3-coder:free",                        128,  True),
    ("Gemini 2.0 Flash (exp)",     "google/gemini-2.0-flash-exp:free",            1000,  True),
    ("Gemini 2.5 Flash (preview)", "google/gemini-2.5-flash-preview:free",        1000,  True),
    ("Llama 3.1 8B",               "meta-llama/llama-3.1-8b-instruct:free",        128,  True),
    ("Mistral 7B",                 "mistralai/mistral-7b-instruct:free",            32,  True),
    ("DeepSeek R1 (free)",         "deepseek/deepseek-r1:free",                    128,  True),
    ("Gemini 2.5 Pro",             "google/gemini-2.5-pro-preview",               1000, False),
    ("Claude Sonnet 4",            "anthropic/claude-sonnet-4",                    200, False),
    ("Claude Opus 4",              "anthropic/claude-opus-4",                      200, False),
    ("GPT-4o mini",                "openai/gpt-4o-mini",                           128, False),
    ("GPT-4o",                     "openai/gpt-4o",                                128, False),
    ("DeepSeek Chat V3",           "deepseek/deepseek-chat-v3-0324",               64, False),
    ("Qwen3 235B (платный)",       "qwen/qwen3-235b-a22b",                        128, False),
    ("Другая (ввести вручную)",    "__custom__",                                     0, False),
]


def _fmt_ctx(ctx_k: int) -> str:
    """Форматирует контекст: 1000k → 1M, 128k → 128k и т.д."""
    if ctx_k >= 1000 and ctx_k % 1000 == 0:
        return f"{ctx_k // 1000}M"
    return f"{ctx_k}k"


def _pick_model_menu(key_val: str) -> str:
    """Показывает numbered меню моделей. Возвращает model_id."""

    # Пробуем подтянуть актуальный список с API
    live_free = _fetch_free_models(key_val)

    print_separator()
    print_info("\n  Выбери модель:\n")

    if live_free:
        print_info("  [dim]— Бесплатные (актуально с OpenRouter) —[/dim]")
        items = live_free[:10]
        for i, (name, mid, ctx) in enumerate(items, 1):
            print_info(f"  [{i:>2}] {name:<38} {_fmt_ctx(ctx)} ctx  [green]бесплатно[/green]")
        offset = len(items) + 1
        print_info("")
        print_info("  [dim]— Платные (кураторский список) —[/dim]")
        paid = [(n, m, c) for n, m, c, free in _CURATED_MODELS if not free and m != "__custom__"]
        for j, (name, mid, ctx) in enumerate(paid, offset):
            print_info(f"  [{j:>2}] {name:<38} {_fmt_ctx(ctx)} ctx")
        all_models = [(n, m, c) for n, m, c in items] + paid
        custom_n = len(all_models) + 1
        print_info(f"  [{custom_n:>2}] Другая (ввести вручную)")
    else:
        for i, (name, mid, ctx, free) in enumerate(_CURATED_MODELS, 1):
            if mid == "__custom__":
                print_info(f"  [{i:>2}] {name}")
                continue
            badge = "[green]бесплатно[/green]" if free else ""
            print_info(f"  [{i:>2}] {name:<38} {_fmt_ctx(ctx)} ctx  {badge}")
        all_models = [(n, m, c) for n, m, c, _ in _CURATED_MODELS if m != "__custom__"]
        custom_n = len(_CURATED_MODELS)

    print_separator()
    while True:
        try:
            choice = input(f"  Номер [1-{custom_n}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "qwen/qwen3-coder:free"

        if choice.isdigit():
            idx = int(choice) - 1
            if live_free:
                merged = [(n, m) for n, m, _ in (live_free[:10] + paid)]  # type: ignore
            else:
                merged = [(n, m) for n, m, _, _ in _CURATED_MODELS if m != "__custom__"]

            if 0 <= idx < len(merged):
                chosen_id = merged[idx][1]
                print_info(f"  Выбрано: [bold]{merged[idx][0]}[/bold]  ({chosen_id})")
                return chosen_id

        # Ввод вручную
        if live_free:
            is_custom = (choice == str(custom_n))
        else:
            is_custom = (choice == str(len(_CURATED_MODELS)))

        if is_custom or not choice.isdigit():
            try:
                m = input("  Введи ID модели: ").strip()
            except (EOFError, KeyboardInterrupt):
                m = ""
            return m or "qwen/qwen3-coder:free"

        print_info("  Неверный номер, попробуй ещё.")


def _fetch_free_models(key_val: str):
    """Запрашивает бесплатные модели у OpenRouter. Возвращает [(name, id, ctx_k)] или []."""
    try:
        import requests
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key_val}"},
            timeout=12,
        )
        if r.status_code != 200:
            return []
        data = r.json().get("data", [])
        free = []
        for m in data:
            p = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 1)) + float(p.get("completion", 1))
            except (TypeError, ValueError):
                continue
            if cost == 0.0:
                ctx_k = (m.get("context_length") or 0) // 1000
                free.append((m.get("name") or m["id"], m["id"], ctx_k))
        free.sort(key=lambda x: -x[2])
        return free[:12]
    except Exception:
        return []


class OpenRouterApiCommand(ICommand):
    name = "/OpenRouter API"
    description = "Управление ключами OpenRouter"
    priority = 2

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config
        while True:
            print_separator()
            print_agent_message("OpenRouter — управление ключами", "system")
            keys = cfg.openrouter_keys
            if not keys:
                print_info("  Ключи не добавлены.")
            else:
                for i, k in enumerate(keys, 1):
                    key_str = k["key"]
                    masked = key_str[:12] + "..." + key_str[-4:] if len(key_str) > 18 else "***"
                    model  = k.get("model") or "не выбрана"
                    role   = k.get("role") or "—"
                    dflt   = " [дефолт]" if k.get("is_default") else ""
                    print_info(f"  [{i}] {masked}  |  {model}  |  роль: {role}{dflt}")
            print_separator()
            print_info("  [1] Добавить ключ")
            print_info("  [2] Удалить ключ")
            print_info("  [3] Сменить модель для ключа")
            print_info("  [0] Назад")
            try:
                choice = input("  Выбери: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "0":
                break

            elif choice == "1":
                try:
                    key_val = input("  Ключ (sk-or-v1-...): ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if not key_val:
                    print_info("  Пусто — отменено.")
                    continue
                print_info("  Загружаю список моделей...")
                model = _pick_model_menu(key_val)
                cfg.add_openrouter_key(key_val, model=model)
                print_info(f"  Ключ добавлен с моделью: {model}")

            elif choice == "2":
                if not keys:
                    print_info("  Нечего удалять.")
                    continue
                try:
                    n = input("  Номер ключа для удаления: ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if n.isdigit() and cfg.remove_openrouter_key(int(n) - 1):
                    print_info("  Удалён.")
                else:
                    print_info("  Неверный номер.")

            elif choice == "3":
                if not keys:
                    print_info("  Нет ключей.")
                    continue
                try:
                    n = input("  Номер ключа: ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if not n.isdigit() or not (0 <= int(n) - 1 < len(keys)):
                    print_info("  Неверный номер.")
                    continue
                k = keys[int(n) - 1]
                model = _pick_model_menu(k["key"])
                if model and cfg.set_openrouter_model(int(n) - 1, model):
                    print_info(f"  Модель обновлена: {model}")
