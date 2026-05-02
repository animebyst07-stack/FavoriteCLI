from .base import ICommand, CommandContext
from ..ui.chat import print_agent_message, print_separator
from ..ui.welcome import print_info


class FavoriteApiCommand(ICommand):
    name = "/Favorite API"
    description = "Управление ключами FavoriteAPI"
    priority = 1

    def execute(self, args: str, ctx: CommandContext) -> None:
        cfg = ctx.config
        while True:
            print_separator()
            print_agent_message("FavoriteAPI — управление ключами", "system")
            keys = cfg.favorite_api_keys
            if not keys:
                print_info("  Ключи не добавлены.")
            else:
                for i, k in enumerate(keys, 1):
                    key_str = k["key"]
                    masked = key_str[:8] + "..." + key_str[-4:] if len(key_str) > 14 else "***"
                    model   = k.get("model") or "дефолтная"
                    role    = k.get("role") or "Не назначено"
                    default = " [дефолт]" if k.get("is_default") else ""
                    print_info(f"  [{i}] {masked}  |  модель: {model}  |  роль: {role}{default}")
            print_separator()
            print_info("  [1] Добавить ключ")
            print_info("  [2] Удалить ключ")
            print_info("  [3] Изменить адрес сервера")
            bridge_status = "настроен" if cfg.has_tg_bridge() else "не настроен"
            print_info(f"  [4] Telegram-мост  ({bridge_status})")
            print_info(f"  [0] Назад  (сервер: {cfg.favorite_api_base_url})")
            try:
                choice = input("  Выбери: ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if choice == "0":
                break
            elif choice == "1":
                try:
                    key_val = input("  Ключ (fa_sk_...): ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if not key_val:
                    print_info("  Пусто — отменено.")
                    continue
                cfg.add_favorite_key(key_val)
                print_info("  Ключ добавлен.")
            elif choice == "2":
                keys = cfg.favorite_api_keys
                if not keys:
                    print_info("  Нечего удалять.")
                    continue
                try:
                    n = input("  Номер ключа для удаления: ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if n.isdigit() and cfg.remove_favorite_key(int(n) - 1):
                    print_info("  Удалён.")
                else:
                    print_info("  Неверный номер.")
            elif choice == "3":
                try:
                    url = input(f"  Новый адрес [{cfg.favorite_api_base_url}]: ").strip()
                except (EOFError, KeyboardInterrupt):
                    continue
                if url:
                    cfg.set_favorite_api_base_url(url)
                    print_info(f"  Адрес обновлён: {url}")
              elif choice == "4":
                  print_info("  TG-мост: при потере связи CLI сам найдёт новый URL через Telegram.")
                  print_info("  Токен бота и Chat ID — те же что в .env FavoriteAPI (TG_NOTIFY_TOKEN, TG_NOTIFY_CHATS).")
                  try:
                      cur_tok = cfg.tg_bridge_token
                      cur_cid = cfg.tg_bridge_chat_id
                      tg_tok = input(f"  Токен бота [{cur_tok[:8]+'...' if cur_tok else 'нет'}]: ").strip()
                      tg_cid = input(f"  Chat ID [{cur_cid or 'нет'}]: ").strip()
                  except (EOFError, KeyboardInterrupt):
                      continue
                  if tg_tok and tg_cid:
                      cfg.set_tg_bridge(tg_tok, tg_cid)
                      print_info("  Мост сохранён. Следующий обрыв — URL подтянется автоматически.")
                  else:
                      print_info("  Отменено (нужны оба поля).")
