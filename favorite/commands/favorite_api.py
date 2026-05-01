from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


class FavoriteApiCommand(ICommand):
    name = "/Favorite API"
    description = "Управление ключами FavoriteAPI"
    priority = 1

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config
        keys = cfg.favorite_api_keys
        print_separator()
        print_agent_message("FavoriteAPI — управление ключами", "system")
        if not keys:
            print_info("  Ключи не добавлены.")
        else:
            for i, k in enumerate(keys, 1):
                masked = k["key"][:12] + "..." + k["key"][-6:]
                model = k.get("model") or "дефолтная"
                role = k.get("role") or "Не назначено"
                default = " [дефолт]" if k.get("is_default") else ""
                print_info(f"  [{i}] {masked}  |  модель: {model}  |  роль: {role}{default}")
        print_separator()
        print_info("  [1] Добавить ключ  [2] Удалить  [3] Назначить роль  [0] Назад")
        choice = input("  Выбери: ").strip()
        if choice == "1":
            key_val = input("  Вставь ключ (fa_sk_...): ").strip()
            if key_val:
                keys.append({"key": key_val, "label": f"key{len(keys)+1}",
                              "model": None, "role": None, "is_default": False})
                cfg.save_keys()
                print_info("  Ключ добавлен.")
