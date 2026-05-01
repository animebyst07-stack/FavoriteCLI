from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


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
                    masked  = key_str[:12] + "..." + key_str[-4:] if len(key_str) > 18 else "***"
                    model   = k.get("model") or "не выбрана"
                    role    = k.get("role") or "Не назначено"
                    default = " [дефолт]" if k.get("is_default") else ""
                    print_info(f"  [{i}] {masked}  |  {model}  |  {role}{default}")
            print_separator()
            print_info("  [1] Добавить ключ")
            print_info("  [2] Удалить ключ")
            print_info("  [3] Сменить модель для ключа")
            print_info("  [4] Список моделей OpenRouter")
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
                try:
                    model = input("  Модель [qwen/qwen3-coder:free]: ").strip() or "qwen/qwen3-coder:free"
                except (EOFError, KeyboardInterrupt):
                    model = "qwen/qwen3-coder:free"
                cfg.add_openrouter_key(key_val, model=model)
                print_info("  Ключ добавлен.")
            elif choice == "2":
                if not keys:
                    print_info("  Нечего удалять.")
                    continue
                try:
                    n = input("  Номер ключа: ").strip()
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
                    n     = input("  Номер ключа: ").strip()
                    model = input("  Новая модель: ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if n.isdigit() and model and cfg.set_openrouter_model(int(n) - 1, model):
                    print_info(f"  Модель обновлена: {model}")
                else:
                    print_info("  Ошибка.")
            elif choice == "4":
                self._show_models(cfg)

    def _show_models(self, cfg) -> None:
        import requests
        key_data = cfg.default_openrouter_key()
        if not key_data:
            print_info("  Нет ключа — сначала добавь через [1].")
            return
        print_info("  Загружаю список моделей OpenRouter...")
        try:
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key_data['key']}"},
                timeout=20,
            )
            models = r.json().get("data", [])
        except Exception as e:
            print_info(f"  Ошибка: {e}")
            return

        def sort_key(m):
            p = m.get("pricing", {})
            try:
                return float(p.get("prompt", 0)) + float(p.get("completion", 0))
            except (TypeError, ValueError):
                return float("inf")

        models.sort(key=sort_key)
        print_info(f"\n  Всего моделей: {len(models)}\n")
        for m in models[:40]:
            ctx_k   = (m.get("context_length") or 0) // 1000
            p       = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 0)) + float(p.get("completion", 0))
                cost_str = f"${cost:.7f}/tok" if cost else "бесплатно"
            except Exception:
                cost_str = "?"
            name = m["id"]
            print_info(f"  {name:<52} ctx:{ctx_k}k  {cost_str}")
        if len(models) > 40:
            print_info(f"\n  ... и ещё {len(models)-40} моделей (используй /models для фильтра)")
