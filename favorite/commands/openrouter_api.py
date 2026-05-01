from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info

# Кураторский список: (display_name, model_id, ctx_k)
# Расположены от дешёвых к дорогим — free модели первые (видно по :free в теге)
_CURATED_MODELS = [
    ("Qwen3 Coder",               "qwen/qwen3-coder:free",                  128),
    ("Gemini 2.5 Flash (preview)", "google/gemini-2.5-flash-preview:free",  1000),
    ("Gemini 2.0 Flash (exp)",     "google/gemini-2.0-flash-exp:free",      1000),
    ("DeepSeek R1",                "deepseek/deepseek-r1:free",              128),
    ("Llama 3.1 8B",               "meta-llama/llama-3.1-8b-instruct:free",  128),
    ("Mistral 7B",                 "mistralai/mistral-7b-instruct:free",      32),
    ("DeepSeek Chat V3",           "deepseek/deepseek-chat-v3-0324",          64),
    ("GPT-4o mini",                "openai/gpt-4o-mini",                     128),
    ("Gemini 2.5 Pro",             "google/gemini-2.5-pro-preview",         1000),
    ("GPT-4o",                     "openai/gpt-4o",                          128),
    ("Claude Sonnet 4",            "anthropic/claude-sonnet-4",              200),
    ("Qwen3 235B",                 "qwen/qwen3-235b-a22b",                   128),
    ("Claude Opus 4",              "anthropic/claude-opus-4",                200),
    ("Другая (ввести вручную)",    "__custom__",                               0),
]


def _fmt_ctx(ctx_k: int) -> str:
    if ctx_k >= 1000 and ctx_k % 1000 == 0:
        return f"{ctx_k // 1000}M"
    return f"{ctx_k}k"


def _fetch_models_sorted(key_val: str):
    """
    Запрашивает модели OpenRouter, сортирует от дешёвых к дорогим.
    Возвращает [(name, id, ctx_k)] или [].
    """
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
        result = []
        for m in data:
            p = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 0)) + float(p.get("completion", 0))
            except (TypeError, ValueError):
                cost = 999.0
            ctx_k = (m.get("context_length") or 0) // 1000
            result.append((m.get("name") or m["id"], m["id"], ctx_k, cost))
        result.sort(key=lambda x: x[3])
        return [(n, mid, ctx) for n, mid, ctx, _ in result[:20]]
    except Exception:
        return []


def _pick_model_menu(key_val: str) -> str:
    """Показывает numbered меню моделей. Возвращает model_id."""
    print_separator()
    print_info("  Загружаю список моделей с OpenRouter...")
    live = _fetch_models_sorted(key_val)

    print_info("\n  Выбери модель:")
    print_info("  [dim]Отсортировано от дешёвых к дорогим. Бесплатные модели имеют тег :free в ID.[/dim]\n")

    if live:
        for i, (name, mid, ctx) in enumerate(live, 1):
            print_info(f"  [{i:>2}] {name:<40} {_fmt_ctx(ctx)} ctx   {mid}")
        custom_n = len(live) + 1
        print_info(f"  [{custom_n:>2}] Другая (ввести вручную)")
        all_models = [(n, m) for n, m, _ in live]
    else:
        print_info("  [dim](не удалось загрузить — показан кураторский список)[/dim]\n")
        curated = [(n, m, c) for n, m, c in _CURATED_MODELS if m != "__custom__"]
        for i, (name, mid, ctx) in enumerate(curated, 1):
            print_info(f"  [{i:>2}] {name:<40} {_fmt_ctx(ctx)} ctx   {mid}")
        custom_n = len(curated) + 1
        print_info(f"  [{custom_n:>2}] Другая (ввести вручную)")
        all_models = [(n, m) for n, m, _ in curated]

    print_separator()
    while True:
        try:
            choice = input(f"  Номер [1-{custom_n}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "qwen/qwen3-coder:free"

        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_models):
                name, mid = all_models[idx]
                print_info(f"  Выбрано: [bold]{name}[/bold]  ({mid})")
                return mid
            if int(choice) == custom_n:
                try:
                    m = input("  Введи ID модели: ").strip()
                except (EOFError, KeyboardInterrupt):
                    m = ""
                return m or "qwen/qwen3-coder:free"

        print_info("  Неверный номер, попробуй ещё.")


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
