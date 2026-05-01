from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info

# Человекочитаемые имена провайдеров по префиксу model_id
_PROVIDER_NAMES = {
    "anthropic":        "Anthropic  (Claude)",
    "openai":           "OpenAI     (GPT)",
    "google":           "Google     (Gemini)",
    "deepseek":         "DeepSeek",
    "qwen":             "Qwen       (Alibaba)",
    "meta-llama":       "Meta       (Llama)",
    "mistralai":        "Mistral",
    "x-ai":             "xAI        (Grok)",
    "groq":             "Groq",
    "cohere":           "Cohere",
    "nvidia":           "NVIDIA",
    "perplexity":       "Perplexity",
    "microsoft":        "Microsoft",
    "amazon":           "Amazon     (Nova)",
    "01-ai":            "01.AI      (Yi)",
    "nousresearch":     "Nous Research",
    "pygmalionai":      "PygmalionAI",
    "sao10k":           "Sao10k",
    "sophosympatheia":  "Sophosympatheia",
    "databricks":       "Databricks",
    "liquid":           "Liquid",
    "inflection":       "Inflection",
}


def _provider_label(prefix: str) -> str:
    return _PROVIDER_NAMES.get(prefix, prefix.capitalize())


def _fmt_ctx(ctx_k: int) -> str:
    if ctx_k >= 1000 and ctx_k % 1000 == 0:
        return f"{ctx_k // 1000}M"
    return f"{ctx_k}k"


def _fetch_all_models(key_val: str) -> dict[str, list]:
    """
    Запрашивает все модели OpenRouter.
    Возвращает словарь {provider_prefix: [(model_id, ctx_k, cost)]},
    отсортированный внутри каждого провайдера от дешёвых к дорогим.
    """
    try:
        import requests
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key_val}"},
            timeout=15,
        )
        if r.status_code != 200:
            return {}
        data = r.json().get("data", [])
        grouped: dict[str, list] = {}
        for m in data:
            mid = m["id"]
            prefix = mid.split("/")[0]
            p = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 0)) + float(p.get("completion", 0))
            except (TypeError, ValueError):
                cost = 999.0
            ctx_k = (m.get("context_length") or 0) // 1000
            grouped.setdefault(prefix, []).append((mid, ctx_k, cost))
        for prefix in grouped:
            grouped[prefix].sort(key=lambda x: x[2])
        return grouped
    except Exception:
        return {}


# Кураторский фоллбэк если нет сети
_CURATED_FALLBACK: dict[str, list] = {
    "google":    [("google/gemini-2.5-flash-preview:free", 1000, 0), ("google/gemini-2.5-pro-preview", 1000, 1)],
    "anthropic": [("anthropic/claude-sonnet-4", 200, 2), ("anthropic/claude-opus-4", 200, 5)],
    "openai":    [("openai/gpt-4o-mini", 128, 1), ("openai/gpt-4o", 128, 3)],
    "deepseek":  [("deepseek/deepseek-r1:free", 128, 0), ("deepseek/deepseek-chat-v3-0324", 64, 1)],
    "qwen":      [("qwen/qwen3-coder:free", 128, 0), ("qwen/qwen3-235b-a22b", 128, 2)],
    "meta-llama":[("meta-llama/llama-3.1-8b-instruct:free", 128, 0)],
    "mistralai": [("mistralai/mistral-7b-instruct:free", 32, 0)],
}


def _pick_model_menu(key_val: str) -> str:
    """Двухуровневое меню: провайдер → модели. Возвращает model_id."""
    print_separator()
    print_info("  Загружаю модели с OpenRouter...")
    grouped = _fetch_all_models(key_val) or _CURATED_FALLBACK
    offline = not bool(_fetch_all_models.__doc__ and grouped is not _CURATED_FALLBACK)

    # Сортируем провайдеров: сначала у кого есть :free модели, потом по алфавиту
    def provider_sort(prefix):
        has_free = any(":free" in mid for mid, _, _ in grouped[prefix])
        return (0 if has_free else 1, _provider_label(prefix))

    providers = sorted(grouped.keys(), key=provider_sort)

    while True:
        print_separator()
        print_info("\n  Шаг 1 — выбери провайдера:\n")
        print_info("  [dim]Провайдеры с бесплатными моделями идут первыми (:free в ID).[/dim]\n")
        for i, prefix in enumerate(providers, 1):
            models = grouped[prefix]
            total  = len(models)
            free_n = sum(1 for mid, _, _ in models if ":free" in mid)
            free_str = f"  {free_n} free" if free_n else ""
            print_info(f"  [{i:>2}] {_provider_label(prefix):<28} {total} моделей{free_str}")
        back_n = len(providers) + 1
        print_info(f"  [{back_n:>2}] Ввести ID вручную")
        print_separator()

        try:
            choice = input(f"  Провайдер [1-{back_n}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            return "qwen/qwen3-coder:free"

        if not choice.isdigit():
            continue
        idx = int(choice) - 1
        if int(choice) == back_n:
            try:
                m = input("  Введи ID модели: ").strip()
            except (EOFError, KeyboardInterrupt):
                m = ""
            return m or "qwen/qwen3-coder:free"
        if not (0 <= idx < len(providers)):
            print_info("  Неверный номер.")
            continue

        # Шаг 2 — модели выбранного провайдера
        prefix  = providers[idx]
        models  = grouped[prefix]

        print_separator()
        print_info(f"\n  Шаг 2 — модели {_provider_label(prefix)}:\n")
        print_info("  [dim]Отсортировано от дешёвых к дорогим.[/dim]\n")
        for j, (mid, ctx, _cost) in enumerate(models, 1):
            print_info(f"  [{j:>2}] {mid:<55} {_fmt_ctx(ctx)} ctx")
        back2 = len(models) + 1
        print_info(f"  [{back2:>2}] ← Назад к провайдерам")
        print_separator()

        try:
            choice2 = input(f"  Модель [1-{back2}]: ").strip()
        except (EOFError, KeyboardInterrupt):
            continue

        if not choice2.isdigit():
            continue
        if int(choice2) == back2:
            continue
        midx = int(choice2) - 1
        if 0 <= midx < len(models):
            chosen = models[midx][0]
            print_info(f"  Выбрано: [bold]{chosen}[/bold]")
            return chosen

        print_info("  Неверный номер.")


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
