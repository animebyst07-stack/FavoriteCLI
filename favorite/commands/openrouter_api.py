from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


class OpenRouterApiCommand(ICommand):
    name = "/OpenRouter API"
    description = "Управление ключами OpenRouter"
    priority = 2

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config
        keys = cfg.openrouter_keys
        print_separator()
        print_agent_message("OpenRouter — управление ключами", "system")
        for i, k in enumerate(keys, 1):
            masked = k["key"][:18] + "..." + k["key"][-6:]
            model = k.get("model") or "не выбрана"
            role = k.get("role") or "Не назначено"
            default = " [дефолт]" if k.get("is_default") else ""
            print_info(f"  [{i}] {masked}  |  модель: {model}  |  роль: {role}{default}")
        print_separator()
        print_info("  [1] Добавить  [2] Список моделей  [0] Назад")
        choice = input("  Выбери: ").strip()
        if choice == "2":
            self._show_models(cfg)

    def _show_models(self, cfg) -> None:
        import requests
        key_data = cfg.default_openrouter_key()
        if not key_data:
            print_info("  Нет ключа OpenRouter.")
            return
        print_info("  Загружаю список моделей...")
        try:
            r = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {key_data['key']}"},
                timeout=15,
            )
            models = r.json().get("data", [])
        except Exception as e:
            print_info(f"  Ошибка: {e}")
            return
        def sort_key(m):
            p = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 0)) + float(p.get("completion", 0))
            except (TypeError, ValueError):
                cost = float("inf")
            return cost
        models.sort(key=sort_key)
        print_info(f"  Всего моделей: {len(models)}")
        for m in models[:30]:
            ctx_k = m.get("context_length", 0) // 1000
            p = m.get("pricing", {})
            try:
                cost = float(p.get("prompt", 0)) + float(p.get("completion", 0))
                cost_str = f"${cost:.6f}/tok"
            except Exception:
                cost_str = "бесплатно"
            print_info(f"  {m['id']:<50} ctx:{ctx_k}k  {cost_str}")
        if len(models) > 30:
            print_info(f"  ... и ещё {len(models)-30} моделей")
